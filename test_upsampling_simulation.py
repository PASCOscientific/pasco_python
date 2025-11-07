"""
Test Upsampling Logic với dữ liệu giả lập
Không cần sensor PASCO thật

Mô phỏng:
- Bluetooth sampling không ổn định (~8Hz với jitter)
- Upsampling lên 50Hz bằng PCHIP
- So sánh raw vs upsampled data
"""

import sys
sys.path.append('src')

import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
import time
from collections import deque


class SimulatedSensor:
    """Mô phỏng sensor PASCO qua Bluetooth"""

    def __init__(self, base_freq=8.0, jitter=0.3):
        self.base_freq = base_freq  # Tần số trung bình
        self.jitter = jitter  # Độ dao động (0-1)
        self.t_start = time.time()
        self.last_sample_time = 0

        # Tạo signal giả: sine wave 2Hz (mô phỏng dao động cầu)
        self.signal_freq = 2.0
        self.amplitude = 0.15  # m/s²
        self.noise_level = 0.01

    def read_sample(self):
        """
        Mô phỏng đọc từ sensor qua Bluetooth
        Tần số không đều do jitter
        """
        # Tính khoảng cách ngẫu nhiên đến sample tiếp theo
        base_dt = 1.0 / self.base_freq
        jitter_dt = np.random.uniform(-self.jitter * base_dt, self.jitter * base_dt)
        dt = base_dt + jitter_dt

        # Đợi để mô phỏng sampling rate
        time.sleep(max(0.001, dt))  # Tối thiểu 1ms

        current_time = time.time() - self.t_start

        # Tạo giá trị: sine wave + noise
        value = (self.amplitude * np.sin(2 * np.pi * self.signal_freq * current_time) +
                 np.random.normal(0, self.noise_level))

        self.last_sample_time = current_time

        return current_time, value


class UpsamplingSimulator:
    """Mô phỏng hệ thống upsampling real-time"""

    def __init__(self, target_fs=50.0):
        self.target_fs = target_fs
        self.raw_data = deque(maxlen=500)
        self.upsampled_data = deque(maxlen=3000)

    def add_raw_sample(self, timestamp, value):
        """Thêm sample vào raw buffer"""
        self.raw_data.append((timestamp, value))

    def upsample_recent(self, current_time, window_s=5.0):
        """Upsample dữ liệu gần đây bằng PCHIP"""
        if len(self.raw_data) < 4:
            return

        # Lấy dữ liệu trong window
        recent_raw = [(t, v) for t, v in self.raw_data if current_time - t <= window_s]

        if len(recent_raw) < 4:
            return

        try:
            timestamps = np.array([t for t, _ in recent_raw])
            values = np.array([v for _, v in recent_raw])

            # PCHIP interpolation
            interpolator = interpolate.PchipInterpolator(timestamps, values)

            # Uniform timestamps
            t_start = timestamps[0]
            t_end = timestamps[-1]
            n_points = int((t_end - t_start) * self.target_fs)

            if n_points < 2:
                return

            uniform_timestamps = np.linspace(t_start, t_end, n_points)
            upsampled_values = interpolator(uniform_timestamps)

            # Chỉ thêm điểm mới
            if self.upsampled_data:
                last_t = self.upsampled_data[-1][0]
                new_points = [(t, v) for t, v in zip(uniform_timestamps, upsampled_values)
                              if t > last_t]
            else:
                new_points = list(zip(uniform_timestamps, upsampled_values))

            for t, v in new_points:
                self.upsampled_data.append((t, float(v)))

        except Exception as e:
            print(f"Upsampling error: {e}")


def run_simulation(duration=10.0, plot=True):
    """
    Chạy simulation

    Args:
        duration: Thời gian simulation (giây)
        plot: Vẽ biểu đồ kết quả
    """
    print("="*60)
    print("SIMULATION: PASCO Sensor Upsampling")
    print("="*60)

    # Tạo simulated sensor
    sensor = SimulatedSensor(base_freq=8.0, jitter=0.3)

    # Tạo upsampling system
    upsampler = UpsamplingSimulator(target_fs=50.0)

    print(f"\nSimulated sensor:")
    print(f"  Base frequency: 8.0 Hz (±30% jitter)")
    print(f"  Signal: 2Hz sine wave, amplitude 0.15 m/s²")
    print(f"\nUpsampling:")
    print(f"  Target frequency: 50 Hz")
    print(f"  Method: PCHIP interpolation")
    print(f"\nCollecting data for {duration}s...\n")

    t_start = time.time()
    sample_count = 0
    last_upsample_time = 0
    upsample_interval = 0.2  # Upsample mỗi 200ms

    # Data collection loop
    while True:
        elapsed = time.time() - t_start
        if elapsed >= duration:
            break

        # Đọc sample từ sensor
        timestamp, value = sensor.read_sample()
        upsampler.add_raw_sample(timestamp, value)
        sample_count += 1

        # Upsample định kỳ
        if elapsed - last_upsample_time >= upsample_interval:
            upsampler.upsample_recent(timestamp)
            last_upsample_time = elapsed

            # Progress
            raw_len = len(upsampler.raw_data)
            ups_len = len(upsampler.upsampled_data)
            actual_freq = sample_count / elapsed if elapsed > 0 else 0
            print(f"  {elapsed:.1f}s | Raw:{raw_len:3d} Up:{ups_len:4d} ~{actual_freq:.1f}Hz")

    # Final upsampling
    upsampler.upsample_recent(timestamp)

    # Statistics
    total_time = time.time() - t_start
    raw_count = len(upsampler.raw_data)
    ups_count = len(upsampler.upsampled_data)
    actual_freq = sample_count / total_time

    print(f"\n{'='*60}")
    print("RESULTS:")
    print(f"{'='*60}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Raw samples: {raw_count}")
    print(f"Upsampled samples: {ups_count}")
    print(f"Actual sampling freq: {actual_freq:.2f} Hz")
    print(f"Upsampling ratio: {ups_count/raw_count:.1f}x")
    print(f"Target freq achieved: {ups_count/total_time:.2f} Hz")

    # Plotting
    if plot and raw_count > 0 and ups_count > 0:
        print(f"\nGenerating plots...")

        fig, axes = plt.subplots(3, 1, figsize=(12, 10))

        # Plot 1: Raw data
        raw_times = [t for t, _ in upsampler.raw_data]
        raw_values = [v for _, v in upsampler.raw_data]

        axes[0].plot(raw_times, raw_values, 'o-', color='#d32f2f',
                     markersize=4, linewidth=1, label='Raw data (~8Hz)')
        axes[0].set_xlabel('Time [s]')
        axes[0].set_ylabel('Acceleration [m/s²]')
        axes[0].set_title('Raw Data (Bluetooth sampling, unstable frequency)')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()

        # Plot 2: Upsampled data
        ups_times = [t for t, _ in upsampler.upsampled_data]
        ups_values = [v for _, v in upsampler.upsampled_data]

        axes[1].plot(ups_times, ups_values, '-', color='#388e3c',
                     linewidth=1.5, label='Upsampled (50Hz, PCHIP)')
        axes[1].set_xlabel('Time [s]')
        axes[1].set_ylabel('Acceleration [m/s²]')
        axes[1].set_title('Upsampled Data (Stable 50Hz)')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()

        # Plot 3: Comparison (overlay)
        axes[2].plot(raw_times, raw_values, 'o', color='#d32f2f',
                     markersize=6, label='Raw samples', alpha=0.6)
        axes[2].plot(ups_times, ups_values, '-', color='#388e3c',
                     linewidth=1.5, label='Upsampled (PCHIP)', alpha=0.8)
        axes[2].set_xlabel('Time [s]')
        axes[2].set_ylabel('Acceleration [m/s²]')
        axes[2].set_title('Comparison: Raw vs Upsampled')
        axes[2].grid(True, alpha=0.3)
        axes[2].legend()

        plt.tight_layout()

        # Save plot
        output_file = 'simulation_result.png'
        plt.savefig(output_file, dpi=150)
        print(f"✓ Plot saved: {output_file}")

        try:
            plt.show()
        except Exception:
            print("  (Cannot display plot in headless environment)")

    print(f"\n{'='*60}")
    print("SIMULATION COMPLETE")
    print(f"{'='*60}\n")

    return upsampler


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║     PASCO Sensor Upsampling - Simulation Test               ║
║                                                              ║
║  Mô phỏng thu thập dữ liệu qua Bluetooth với upsampling     ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Run simulation
    upsampler = run_simulation(duration=10.0, plot=True)

    print("\nNOTE:")
    print("  - Simulation này mô phỏng hành vi của sensor PASCO thật")
    print("  - Tần số raw ~8Hz với jitter (giống Bluetooth)")
    print("  - Upsampling lên 50Hz với PCHIP interpolation")
    print("  - Để test với sensor thật, chạy trên máy có Bluetooth")
