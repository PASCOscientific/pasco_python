"""
Data Reconstruction for Undersampled Oscillation Data

Vấn đề: Sensor chỉ lấy mẫu ~8Hz, không đủ để capture dao động nhanh (>4Hz)
Giải pháp: Model-based reconstruction using FFT and physics assumptions
"""

import numpy as np
from scipy import signal, optimize
from scipy.interpolate import PchipInterpolator
import matplotlib.pyplot as plt


class OscillationReconstructor:
    """
    Tái tạo dao động từ dữ liệu undersampled

    Methods:
    1. FFT-based: Phân tích tần số chính, tái tạo sin waves
    2. Harmonic fit: Fit multiple sin/cos components
    3. Physics-based: Dùng mô hình vật lý (damped oscillation, etc.)
    """

    def __init__(self, timestamps, values):
        """
        Args:
            timestamps: array of time points (có thể không đều)
            values: array of measurement values
        """
        self.timestamps = np.array(timestamps)
        self.values = np.array(values)
        self.dt_avg = np.mean(np.diff(self.timestamps))
        self.fs_avg = 1.0 / self.dt_avg if self.dt_avg > 0 else 10.0

    def method1_fft_based(self, target_fs=100.0):
        """
        Method 1: FFT-based reconstruction

        Ý tưởng:
        - Phân tích FFT để tìm dominant frequencies
        - Tái tạo signal bằng tổng các sin waves
        - Thêm noise nhỏ để realistic

        Giới hạn: Chỉ hoạt động tốt nếu sampling rate > 2x freq cao nhất
        """
        # Resample về uniform grid trước
        t_uniform = np.linspace(self.timestamps[0], self.timestamps[-1], len(self.timestamps))
        interp = PchipInterpolator(self.timestamps, self.values)
        v_uniform = interp(t_uniform)

        # FFT analysis
        fft_vals = np.fft.rfft(v_uniform - np.mean(v_uniform))
        fft_freqs = np.fft.rfftfreq(len(v_uniform), d=self.dt_avg)
        fft_mags = np.abs(fft_vals)

        # Tìm dominant frequencies (top 5)
        top_indices = np.argsort(fft_mags)[-5:][::-1]
        dominant_freqs = fft_freqs[top_indices]
        dominant_mags = fft_mags[top_indices]
        dominant_phases = np.angle(fft_vals[top_indices])

        # Tái tạo signal với tần số cao hơn
        t_new = np.arange(self.timestamps[0], self.timestamps[-1], 1.0/target_fs)
        signal_reconstructed = np.mean(self.values) * np.ones_like(t_new)

        for freq, mag, phase in zip(dominant_freqs, dominant_mags, dominant_phases):
            if freq > 0:  # Skip DC component
                amplitude = 2 * mag / len(v_uniform)
                signal_reconstructed += amplitude * np.sin(2 * np.pi * freq * t_new + phase)

        return t_new, signal_reconstructed

    def method2_harmonic_fit(self, target_fs=100.0, n_harmonics=3):
        """
        Method 2: Fit multiple harmonic components

        Ý tưởng:
        - Fit sum of sin waves: y = A0 + A1*sin(w1*t + phi1) + A2*sin(w2*t + phi2) + ...
        - Optimize parameters để match measured data
        - Generate high-rate signal

        Tốt hơn FFT vì:
        - Xử lý được non-uniform sampling
        - Có thể constrain frequencies dựa trên physics
        """
        def multi_sine(t, *params):
            """
            params = [A0, A1, f1, phi1, A2, f2, phi2, ...]
            """
            result = params[0]  # DC offset
            for i in range(n_harmonics):
                A = params[1 + i*3]
                f = params[2 + i*3]
                phi = params[3 + i*3]
                result += A * np.sin(2 * np.pi * f * t + phi)
            return result

        # Initial guess từ FFT
        v_mean = np.mean(self.values)
        v_std = np.std(self.values)
        f_guess = 1.0  # 1 Hz initial guess

        # params: [A0, A1, f1, phi1, A2, f2, phi2, ...]
        p0 = [v_mean]
        for i in range(n_harmonics):
            p0.extend([v_std / (i+1), f_guess * (i+1), 0.0])

        # Fit
        try:
            popt, _ = optimize.curve_fit(
                multi_sine,
                self.timestamps,
                self.values,
                p0=p0,
                maxfev=5000
            )

            # Generate high-rate signal
            t_new = np.arange(self.timestamps[0], self.timestamps[-1], 1.0/target_fs)
            signal_reconstructed = multi_sine(t_new, *popt)

            # Extract fitted parameters
            fitted_params = {
                'DC_offset': popt[0],
                'harmonics': []
            }
            for i in range(n_harmonics):
                fitted_params['harmonics'].append({
                    'amplitude': popt[1 + i*3],
                    'frequency_Hz': popt[2 + i*3],
                    'phase_rad': popt[3 + i*3]
                })

            return t_new, signal_reconstructed, fitted_params

        except Exception as e:
            print(f"Harmonic fit failed: {e}")
            # Fallback to simple interpolation
            t_new = np.arange(self.timestamps[0], self.timestamps[-1], 1.0/target_fs)
            interp = PchipInterpolator(self.timestamps, self.values)
            return t_new, interp(t_new), None

    def method3_physics_damped(self, target_fs=100.0):
        """
        Method 3: Physics-based damped oscillation

        Mô hình: y(t) = A * exp(-γ*t) * sin(ω*t + φ) + y0

        Phù hợp cho:
        - Con lắc dao động tắt dần
        - Spring-mass systems with damping
        - Các hệ có ma sát
        """
        def damped_sine(t, A, gamma, omega, phi, y0):
            return A * np.exp(-gamma * t) * np.sin(omega * t + phi) + y0

        # Shift time to start from 0
        t_shifted = self.timestamps - self.timestamps[0]

        # Initial guess
        A_guess = (np.max(self.values) - np.min(self.values)) / 2
        y0_guess = np.mean(self.values)
        omega_guess = 2 * np.pi * 1.0  # 1 Hz
        gamma_guess = 0.1  # Light damping
        phi_guess = 0.0

        try:
            popt, _ = optimize.curve_fit(
                damped_sine,
                t_shifted,
                self.values,
                p0=[A_guess, gamma_guess, omega_guess, phi_guess, y0_guess],
                maxfev=10000
            )

            # Generate high-rate signal
            t_new_shifted = np.arange(0, t_shifted[-1], 1.0/target_fs)
            signal_reconstructed = damped_sine(t_new_shifted, *popt)
            t_new = t_new_shifted + self.timestamps[0]

            # Extract parameters
            fitted_params = {
                'amplitude': popt[0],
                'damping_coef': popt[1],
                'angular_freq': popt[2],
                'frequency_Hz': popt[2] / (2 * np.pi),
                'phase_rad': popt[3],
                'offset': popt[4],
                'quality_factor': popt[2] / (2 * popt[1]) if popt[1] > 0 else float('inf')
            }

            return t_new, signal_reconstructed, fitted_params

        except Exception as e:
            print(f"Physics fit failed: {e}")
            # Fallback
            t_new = np.arange(self.timestamps[0], self.timestamps[-1], 1.0/target_fs)
            interp = PchipInterpolator(self.timestamps, self.values)
            return t_new, interp(t_new), None

    def compare_methods(self, target_fs=100.0):
        """
        So sánh tất cả methods và visualize
        """
        fig, axes = plt.subplots(4, 1, figsize=(12, 10))

        # Original data
        axes[0].plot(self.timestamps, self.values, 'o-', label='Original (sampled)', markersize=8)
        axes[0].set_title(f'Original Data (avg {self.fs_avg:.1f} Hz)')
        axes[0].set_xlabel('Time [s]')
        axes[0].set_ylabel('Value')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Method 1: FFT-based
        try:
            t1, v1 = self.method1_fft_based(target_fs)
            axes[1].plot(self.timestamps, self.values, 'o', label='Original', markersize=8, alpha=0.5)
            axes[1].plot(t1, v1, '-', label=f'FFT-based ({target_fs} Hz)', linewidth=1)
            axes[1].set_title('Method 1: FFT-based Reconstruction')
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)
        except Exception as e:
            axes[1].text(0.5, 0.5, f'Method 1 failed: {e}', transform=axes[1].transAxes)

        # Method 2: Harmonic fit
        try:
            t2, v2, params2 = self.method2_harmonic_fit(target_fs, n_harmonics=3)
            axes[2].plot(self.timestamps, self.values, 'o', label='Original', markersize=8, alpha=0.5)
            axes[2].plot(t2, v2, '-', label=f'Harmonic fit ({target_fs} Hz)', linewidth=1)
            axes[2].set_title('Method 2: Multi-Harmonic Fit')
            if params2:
                freqs = [f"{h['frequency_Hz']:.2f}Hz" for h in params2['harmonics'][:3]]
                info = f"Freqs: {freqs}"
                axes[2].text(0.02, 0.98, info, transform=axes[2].transAxes,
                           verticalalignment='top', fontsize=8, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)
        except Exception as e:
            axes[2].text(0.5, 0.5, f'Method 2 failed: {e}', transform=axes[2].transAxes)

        # Method 3: Physics damped
        try:
            t3, v3, params3 = self.method3_physics_damped(target_fs)
            axes[3].plot(self.timestamps, self.values, 'o', label='Original', markersize=8, alpha=0.5)
            axes[3].plot(t3, v3, '-', label=f'Damped oscillation ({target_fs} Hz)', linewidth=1)
            axes[3].set_title('Method 3: Physics-based (Damped Oscillation)')
            if params3:
                info = f"f={params3['frequency_Hz']:.2f}Hz, γ={params3['damping_coef']:.3f}, Q={params3['quality_factor']:.1f}"
                axes[3].text(0.02, 0.98, info, transform=axes[3].transAxes,
                           verticalalignment='top', fontsize=8, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
            axes[3].legend()
            axes[3].grid(True, alpha=0.3)
        except Exception as e:
            axes[3].text(0.5, 0.5, f'Method 3 failed: {e}', transform=axes[3].transAxes)

        axes[3].set_xlabel('Time [s]')
        plt.tight_layout()
        return fig


# Example usage
if __name__ == '__main__':
    # Simulate undersampled oscillation
    print("Simulating undersampled oscillation...")

    # True signal: 5 Hz damped oscillation
    t_true = np.linspace(0, 5, 500)  # 5 seconds @ 100 Hz
    true_signal = 2.0 * np.exp(-0.2 * t_true) * np.sin(2 * np.pi * 5.0 * t_true) + 10.0

    # Undersampled: ~8 Hz with jitter
    t_sampled = []
    t = 0
    while t < 5:
        t_sampled.append(t)
        dt = 0.125 + np.random.uniform(-0.02, 0.02)  # 8Hz ± jitter
        t += dt
    t_sampled = np.array(t_sampled)

    # Sample the true signal
    sampled_values = 2.0 * np.exp(-0.2 * t_sampled) * np.sin(2 * np.pi * 5.0 * t_sampled) + 10.0
    sampled_values += np.random.normal(0, 0.05, len(t_sampled))  # Add noise

    print(f"Original signal: 100 Hz, 5.0 Hz oscillation")
    print(f"Sampled signal: ~{1/np.mean(np.diff(t_sampled)):.1f} Hz (undersampled!)")

    # Reconstruct
    reconstructor = OscillationReconstructor(t_sampled, sampled_values)
    fig = reconstructor.compare_methods(target_fs=100.0)

    plt.savefig('reconstruction_comparison.png', dpi=150, bbox_inches='tight')
    print("\nSaved comparison plot to: reconstruction_comparison.png")
    plt.show()
