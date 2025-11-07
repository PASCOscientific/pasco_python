"""
Data Upsampling Tool for PASCO Sensors
========================================

Tăng tần số dữ liệu từ sensors PASCO bằng các phương pháp nội suy.

Các phương pháp:
1. Linear Interpolation - Nội suy tuyến tính (đơn giản, nhanh)
2. Cubic Spline - Nội suy đường cong trơn (smooth)
3. Polynomial - Nội suy đa thức
4. PCHIP - Preserving monotonicity (giữ tính đơn điệu)

Lưu ý: Upsampling KHÔNG tạo thông tin mới, chỉ ước lượng giá trị giữa các mẫu.
"""

import sys
sys.path.append('src')

import numpy as np
from scipy import interpolate
import time
import csv
from datetime import datetime


class DataUpsampler:
    """
    Nội suy dữ liệu từ tần số thấp lên tần số cao hơn
    """

    def __init__(self, original_data, original_freq):
        """
        Args:
            original_data: dict {'timestamp': [...], 'value': [...]}
            original_freq: tần số gốc (Hz)
        """
        self.timestamps = np.array(original_data['timestamp'])
        self.values = np.array(original_data['value'])
        self.original_freq = original_freq

    def upsample(self, target_freq, method='cubic'):
        """
        Nội suy dữ liệu lên tần số cao hơn

        Args:
            target_freq: tần số mục tiêu (Hz)
            method: 'linear', 'cubic', 'pchip', 'polynomial'

        Returns:
            dict {'timestamp': [...], 'value': [...], 'method': str}
        """
        if target_freq <= self.original_freq:
            print(f"Cảnh báo: Tần số mục tiêu ({target_freq}Hz) <= tần số gốc ({self.original_freq}Hz)")
            return {'timestamp': self.timestamps, 'value': self.values, 'method': 'original'}

        # Tạo mảng timestamp mới với tần số cao
        t_start = self.timestamps[0]
        t_end = self.timestamps[-1]
        duration = t_end - t_start
        n_new_samples = int(duration * target_freq)

        new_timestamps = np.linspace(t_start, t_end, n_new_samples)

        # Chọn phương pháp nội suy
        if method == 'linear':
            interp_func = interpolate.interp1d(self.timestamps, self.values, kind='linear')
            new_values = interp_func(new_timestamps)

        elif method == 'cubic':
            interp_func = interpolate.interp1d(self.timestamps, self.values, kind='cubic')
            new_values = interp_func(new_timestamps)

        elif method == 'pchip':
            interp_func = interpolate.PchipInterpolator(self.timestamps, self.values)
            new_values = interp_func(new_timestamps)

        elif method == 'polynomial':
            # Fit polynomial degree = min(len(data)-1, 5)
            degree = min(len(self.timestamps) - 1, 5)
            coeffs = np.polyfit(self.timestamps, self.values, degree)
            poly = np.poly1d(coeffs)
            new_values = poly(new_timestamps)

        else:
            raise ValueError(f"Unknown method: {method}")

        return {
            'timestamp': new_timestamps.tolist(),
            'value': new_values.tolist(),
            'method': method,
            'original_freq': self.original_freq,
            'target_freq': target_freq,
            'original_samples': len(self.timestamps),
            'new_samples': len(new_timestamps)
        }

    def compare_methods(self, target_freq):
        """
        So sánh tất cả các phương pháp nội suy
        """
        methods = ['linear', 'cubic', 'pchip']
        results = {}

        print(f"\n{'='*60}")
        print(f"SO SÁNH CÁC PHƯƠNG PHÁP UPSAMPLING")
        print(f"{'='*60}")
        print(f"Tần số gốc: {self.original_freq} Hz ({len(self.timestamps)} mẫu)")
        print(f"Tần số mục tiêu: {target_freq} Hz")
        print(f"Thời lượng: {self.timestamps[-1] - self.timestamps[0]:.2f}s")
        print(f"{'='*60}\n")

        for method in methods:
            start_time = time.time()
            result = self.upsample(target_freq, method=method)
            elapsed = time.time() - start_time

            results[method] = result

            print(f"{method.upper():12s} | "
                  f"Mẫu mới: {result['new_samples']:5d} | "
                  f"Tỷ lệ: {result['new_samples']/result['original_samples']:.1f}x | "
                  f"Thời gian: {elapsed*1000:.2f}ms")

        return results


def demo_with_synthetic_data():
    """
    Demo với dữ liệu giả lập (sine wave + noise)
    """
    print("\n" + "="*60)
    print("DEMO: Upsampling với dữ liệu giả lập")
    print("="*60)

    # Tạo dữ liệu giả lập: sine wave ở 8Hz
    original_freq = 8  # Hz
    duration = 5  # seconds
    n_samples = int(original_freq * duration)

    timestamps = np.linspace(0, duration, n_samples)
    # Sine wave 2Hz + một chút noise
    values = np.sin(2 * np.pi * 2 * timestamps) + np.random.normal(0, 0.1, n_samples)

    original_data = {
        'timestamp': timestamps.tolist(),
        'value': values.tolist()
    }

    # Tạo upsampler
    upsampler = DataUpsampler(original_data, original_freq)

    # So sánh các phương pháp, tăng lên 50Hz
    target_freq = 50
    results = upsampler.compare_methods(target_freq)

    # Lưu kết quả
    output_dir = 'upsampling_results'
    import os
    os.makedirs(output_dir, exist_ok=True)

    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Lưu dữ liệu gốc
    with open(f'{output_dir}/original_{timestamp_str}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'value'])
        for t, v in zip(timestamps, values):
            writer.writerow([t, v])

    # Lưu từng phương pháp
    for method, result in results.items():
        filename = f'{output_dir}/{method}_{target_freq}Hz_{timestamp_str}.csv'
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'value'])
            for t, v in zip(result['timestamp'], result['value']):
                writer.writerow([t, v])
        print(f"\n✓ Đã lưu: {filename}")

    print(f"\n{'='*60}")
    print("KẾT LUẬN:")
    print(f"{'='*60}")
    print("• LINEAR: Nhanh nhất, đơn giản, nhưng có góc nhọn tại các điểm mẫu")
    print("• CUBIC: Trơn tru hơn, phù hợp với tín hiệu liên tục")
    print("• PCHIP: Giữ tính đơn điệu, tránh overshoot, tốt cho sensor data")
    print(f"{'='*60}\n")

    return results


def upsample_from_pasco_data(data_list, target_freq, measurement_key='Temperature'):
    """
    Upsampling dữ liệu thực từ PASCO sensor

    Args:
        data_list: list of dicts from streaming_test.py
                   [{'timestamp': 0.0, 'Temperature': 23.5, ...}, ...]
        target_freq: tần số mục tiêu (Hz)
        measurement_key: tên measurement cần upsample

    Returns:
        upsampled data
    """
    # Trích xuất timestamp và values
    timestamps = [d['timestamp'] for d in data_list]
    values = [d.get(measurement_key, 0) for d in data_list]

    # Tính tần số gốc
    if len(timestamps) > 1:
        duration = timestamps[-1] - timestamps[0]
        original_freq = len(timestamps) / duration
    else:
        original_freq = 1.0

    print(f"\nDữ liệu PASCO:")
    print(f"  - Measurement: {measurement_key}")
    print(f"  - Số mẫu: {len(timestamps)}")
    print(f"  - Thời lượng: {duration:.2f}s")
    print(f"  - Tần số ước lượng: {original_freq:.2f} Hz")

    original_data = {
        'timestamp': timestamps,
        'value': values
    }

    upsampler = DataUpsampler(original_data, original_freq)
    result = upsampler.upsample(target_freq, method='pchip')  # PCHIP tốt cho sensor

    # Convert về định dạng giống input
    upsampled_list = []
    for t, v in zip(result['timestamp'], result['value']):
        upsampled_list.append({
            'timestamp': t,
            measurement_key: v
        })

    print(f"\nKết quả Upsampling:")
    print(f"  - Phương pháp: {result['method']}")
    print(f"  - Tần số mới: {target_freq} Hz")
    print(f"  - Số mẫu mới: {result['new_samples']}")
    print(f"  - Tỷ lệ: {result['new_samples']/result['original_samples']:.1f}x")

    return upsampled_list


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║         PASCO Data Upsampling Tool                           ║
║                                                              ║
║  Tăng tần số dữ liệu sensor bằng các phương pháp nội suy    ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Chạy demo
    demo_with_synthetic_data()

    print("\n" + "="*60)
    print("CÁCH SỬ DỤNG VỚI DỮ LIỆU THỰC:")
    print("="*60)
    print("""
from data_upsampling import upsample_from_pasco_data

# Sau khi thu thập dữ liệu từ sensor
# data = sensor.fast_polling_mode(['Temperature'], duration=10)

# Upsampling lên 50Hz
# upsampled = upsample_from_pasco_data(data, target_freq=50,
#                                       measurement_key='Temperature')

# Lưu file
# import csv
# with open('upsampled_data.csv', 'w', newline='') as f:
#     writer = csv.DictWriter(f, fieldnames=['timestamp', 'Temperature'])
#     writer.writeheader()
#     writer.writerows(upsampled)
    """)
