"""
Thu thập dữ liệu từ PASCO sensor và upsampling lên tần số cao hơn
==================================================================

Workflow:
1. Kết nối với sensor PASCO
2. Thu thập dữ liệu ở tần số thực (~5-10Hz)
3. Upsampling lên 50Hz hoặc 100Hz
4. Lưu cả dữ liệu gốc và upsampled
"""

import sys
sys.path.append('src')

from pasco.pasco_ble_device import PASCOBLEDevice
from data_upsampling import upsample_from_pasco_data
import time
import csv
from datetime import datetime
import os


class PASCODataCollector:
    """
    Thu thập dữ liệu từ PASCO sensor với fast polling
    """

    def __init__(self):
        self.sensor = PASCOBLEDevice()
        self.connected = False

    def connect(self, sensor_id):
        """
        Kết nối với sensor bằng 6-digit ID

        Args:
            sensor_id: str, ví dụ '123-456'
        """
        print(f"\n🔍 Đang kết nối với sensor: {sensor_id}")

        attempt = 0
        max_attempts = 5

        while attempt < max_attempts:
            try:
                attempt += 1
                self.sensor.connect_by_id(sensor_id)
                self.connected = True
                print(f"✓ Đã kết nối với sensor {sensor_id}")

                # Hiển thị thông tin sensor
                measurements = self.sensor.get_measurement_list()
                print(f"\n📊 Measurements có sẵn: {measurements}")

                return True
            except Exception as e:
                print(f"   Thử lần {attempt}/{max_attempts}: {str(e)[:50]}")
                time.sleep(1)

        print(f"✗ Không thể kết nối với sensor {sensor_id}")
        return False

    def scan_and_connect(self, device_filter=None):
        """
        Scan và kết nối với sensor

        Args:
            device_filter: str, tìm sensor có tên chứa chuỗi này
        """
        print(f"\n🔍 Đang scan sensors...")
        found_devices = self.sensor.scan(device_filter)

        if not found_devices:
            print("✗ Không tìm thấy sensor nào")
            return False

        print(f"\n📡 Tìm thấy {len(found_devices)} sensor(s):")
        for i, device in enumerate(found_devices):
            print(f"  {i}: {device.name} ({device.address})")

        if len(found_devices) == 1:
            selected = 0
        else:
            selected = int(input("\nChọn sensor (số): "))

        try:
            self.sensor.connect(found_devices[selected])
            self.connected = True
            print(f"✓ Đã kết nối với {found_devices[selected].name}")

            measurements = self.sensor.get_measurement_list()
            print(f"\n📊 Measurements: {measurements}")

            return True
        except Exception as e:
            print(f"✗ Lỗi kết nối: {e}")
            return False

    def collect_data(self, measurements, duration=10, verbose=True):
        """
        Thu thập dữ liệu bằng fast polling

        Args:
            measurements: list of measurement names
            duration: thời gian thu thập (giây)
            verbose: hiển thị tiến trình

        Returns:
            list of dicts [{'timestamp': t, 'Measurement1': v1, ...}, ...]
        """
        if not self.connected:
            print("✗ Chưa kết nối với sensor")
            return []

        print(f"\n📊 Bắt đầu thu thập dữ liệu...")
        print(f"   Measurements: {measurements}")
        print(f"   Thời gian: {duration}s")
        print(f"   {'─'*50}")

        all_data = []
        start_time = time.time()
        last_update = start_time

        try:
            while (time.time() - start_time) < duration:
                try:
                    # Đọc dữ liệu
                    data_point = {}
                    data_point['timestamp'] = time.time() - start_time

                    for m in measurements:
                        value = self.sensor.read_data(m)
                        data_point[m] = value

                    all_data.append(data_point)

                    # Hiển thị tiến trình mỗi 1s
                    if verbose and (time.time() - last_update) >= 1.0:
                        elapsed = time.time() - start_time
                        freq = len(all_data) / elapsed if elapsed > 0 else 0
                        print(f"   {elapsed:.1f}s | {len(all_data)} mẫu | ~{freq:.1f} Hz")
                        last_update = time.time()

                except Exception as e:
                    if verbose:
                        print(f"   ⚠ Lỗi đọc: {e}")

            # Kết thúc
            total_time = time.time() - start_time
            avg_freq = len(all_data) / total_time if total_time > 0 else 0

            print(f"   {'─'*50}")
            print(f"✓ Hoàn tất: {len(all_data)} mẫu | {avg_freq:.2f} Hz")

            return all_data

        except KeyboardInterrupt:
            print(f"\n⚠ Dừng thu thập bởi người dùng")
            return all_data

    def disconnect(self):
        """Ngắt kết nối sensor"""
        if self.connected:
            self.sensor.disconnect()
            self.connected = False
            print("✓ Đã ngắt kết nối sensor")


def save_data(data, filename, measurements):
    """
    Lưu dữ liệu ra CSV

    Args:
        data: list of dicts
        filename: tên file output
        measurements: list of measurement names
    """
    fieldnames = ['timestamp'] + measurements

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"✓ Đã lưu: {filename} ({len(data)} mẫu)")


def main_workflow(sensor_id, measurements, duration=10, target_freq=50, upsample_method='pchip'):
    """
    Workflow hoàn chỉnh: Thu thập -> Upsampling -> Lưu file

    Args:
        sensor_id: str, 6-digit sensor ID (hoặc None để scan)
        measurements: list of str, tên measurements
        duration: thời gian thu thập (s)
        target_freq: tần số upsampling mục tiêu (Hz)
        upsample_method: 'linear', 'cubic', 'pchip'
    """
    print("=" * 70)
    print("PASCO DATA COLLECTION & UPSAMPLING WORKFLOW")
    print("=" * 70)

    # Tạo output folder
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f'data_output/{timestamp_str}'
    os.makedirs(output_dir, exist_ok=True)

    # 1. Kết nối sensor
    collector = PASCODataCollector()

    if sensor_id:
        success = collector.connect(sensor_id)
    else:
        success = collector.scan_and_connect()

    if not success:
        print("✗ Không thể kết nối. Thoát.")
        return

    # 2. Thu thập dữ liệu gốc
    original_data = collector.collect_data(measurements, duration=duration)

    if not original_data:
        print("✗ Không có dữ liệu. Thoát.")
        collector.disconnect()
        return

    # Lưu dữ liệu gốc
    original_file = f'{output_dir}/original_data.csv'
    save_data(original_data, original_file, measurements)

    # 3. Upsampling cho từng measurement
    print(f"\n{'='*70}")
    print(f"UPSAMPLING DỮ LIỆU")
    print(f"{'='*70}")

    for measurement in measurements:
        print(f"\n📈 Measurement: {measurement}")
        print(f"   Phương pháp: {upsample_method}")
        print(f"   Tần số mục tiêu: {target_freq} Hz")

        # Upsampling
        upsampled = upsample_from_pasco_data(
            original_data,
            target_freq=target_freq,
            measurement_key=measurement
        )

        # Lưu
        upsampled_file = f'{output_dir}/{measurement}_{upsample_method}_{target_freq}Hz.csv'
        save_data(upsampled, upsampled_file, [measurement])

    # 4. Ngắt kết nối
    collector.disconnect()

    # Summary
    print(f"\n{'='*70}")
    print(f"HOÀN TẤT")
    print(f"{'='*70}")
    print(f"📁 Thư mục output: {output_dir}")
    print(f"📊 Số measurements: {len(measurements)}")
    print(f"🔢 Dữ liệu gốc: {len(original_data)} mẫu")
    print(f"🔢 Dữ liệu upsampled: ~{int(len(original_data) * target_freq / (len(original_data)/duration))} mẫu/measurement")
    print(f"{'='*70}\n")


# ============================================================
# DEMO MODE - Không cần sensor thật
# ============================================================

def demo_without_sensor(target_freq=50):
    """
    Demo upsampling với dữ liệu giả (không cần sensor)
    """
    import numpy as np

    print("=" * 70)
    print("DEMO MODE: Upsampling với dữ liệu giả lập")
    print("=" * 70)

    # Tạo dữ liệu giả: Temperature oscillating around 23°C
    duration = 10  # seconds
    original_freq = 8  # Hz (giống sensor thật)
    n_samples = int(duration * original_freq)

    timestamps = np.linspace(0, duration, n_samples)
    # Temperature: 23°C + 2°C sine wave + noise
    temperatures = 23 + 2 * np.sin(2 * np.pi * 0.5 * timestamps) + np.random.normal(0, 0.2, n_samples)

    original_data = []
    for t, temp in zip(timestamps, temperatures):
        original_data.append({
            'timestamp': t,
            'Temperature': temp
        })

    print(f"\n📊 Dữ liệu giả lập:")
    print(f"   - Thời lượng: {duration}s")
    print(f"   - Tần số gốc: {original_freq} Hz")
    print(f"   - Số mẫu: {len(original_data)}")

    # Lưu dữ liệu gốc
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f'data_output/demo_{timestamp_str}'
    os.makedirs(output_dir, exist_ok=True)

    original_file = f'{output_dir}/demo_original.csv'
    save_data(original_data, original_file, ['Temperature'])

    # Upsampling
    print(f"\n📈 Upsampling lên {target_freq} Hz...")
    upsampled = upsample_from_pasco_data(
        original_data,
        target_freq=target_freq,
        measurement_key='Temperature'
    )

    # Lưu upsampled
    upsampled_file = f'{output_dir}/demo_upsampled_{target_freq}Hz.csv'
    save_data(upsampled, upsampled_file, ['Temperature'])

    print(f"\n✓ Demo hoàn tất! Kiểm tra thư mục: {output_dir}")


if __name__ == '__main__':
    import sys

    print("""
╔══════════════════════════════════════════════════════════════╗
║   PASCO Data Collection & Upsampling                         ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Kiểm tra arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        # Demo mode
        demo_without_sensor(target_freq=50)

    elif len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
CÁCH SỬ DỤNG:

1. Demo mode (không cần sensor):
   python collect_and_upsample.py --demo

2. Với sensor thật (cần có sensor ID):
   python collect_and_upsample.py

   Sau đó edit code và chạy:
   main_workflow(
       sensor_id='123-456',           # Thay bằng ID sensor của bạn
       measurements=['Temperature'],   # Chọn measurements
       duration=10,                    # Thời gian thu (giây)
       target_freq=50,                 # Tần số upsampling (Hz)
       upsample_method='pchip'         # linear, cubic, hoặc pchip
   )

3. Scan sensor:
   main_workflow(
       sensor_id=None,                # Sẽ scan và chọn
       measurements=['Temperature'],
       duration=10,
       target_freq=50
   )
        """)

    else:
        # Mặc định: chạy demo
        print("⚠ Không có sensor ID. Chạy demo mode...\n")
        print("💡 Dùng --help để xem hướng dẫn\n")
        demo_without_sensor(target_freq=50)
