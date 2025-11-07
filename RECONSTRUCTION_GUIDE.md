# Hướng dẫn Tái Tạo Dao Động từ Dữ Liệu Undersampled

## Vấn đề

Bạn nói đúng! **Upsampling (PCHIP) chỉ nội suy giữa các điểm đã có, không thể tái tạo dao động bị bỏ lỡ.**

### Ví dụ:

```
Tín hiệu thực (10 Hz oscillation):
    /\  /\  /\  /\  /\  /\  /\  /\  /\  /\
   /  \/  \/  \/  \/  \/  \/  \/  \/  \/  \

Sensor chỉ thấy (8 Hz sampling):
    *           *           *           *

PCHIP upsampling:
    *------.-----*------.-----*------.-----*
          ^^^^^ Mất hết dao động giữa! SAI!
```

**Nguyên lý Nyquist**: Để capture tín hiệu có tần số `f`, cần sampling rate ≥ `2f`.

- Nếu vật dao động 10 Hz → Cần ≥20 Hz sampling
- Sensor chỉ có ~8 Hz → **Aliasing, mất thông tin**

## Giải pháp

### Cách 1: Tăng Tần Số Sensor (Tốt nhất)

Hiện tại sensor PASCO qua Bluetooth chỉ đạt ~8Hz. **Không có cách nào tăng được**.

### Cách 2: Model-Based Reconstruction (Thực tế)

Dùng **kiến thức vật lý** và **pattern recognition** để tái tạo dao động.

Module `data_reconstruction.py` cung cấp **3 phương pháp**:

## 3 Phương Pháp Reconstruction

### Method 1: FFT-Based 🔊

**Ý tưởng**: Phân tích tần số chính (FFT), tái tạo tín hiệu bằng tổng sin waves.

**Ưu điểm**:
- Nhanh
- Tốt cho tín hiệu tuần hoàn

**Nhược điểm**:
- Chỉ hoạt động nếu sampling rate đủ cao (>= Nyquist limit)
- Không xử lý được aliasing nặng

**Khi nào dùng**: Khi tần số dao động < sampling rate / 2

```python
from data_reconstruction import OscillationReconstructor

# Load your data
t_new, v_new = reconstructor.method1_fft_based(target_fs=100.0)
```

### Method 2: Multi-Harmonic Fit 🎵

**Ý tưởng**: Fit tổng nhiều sin waves với curve fitting optimization.

Model: `y(t) = A0 + A1*sin(2πf1*t + φ1) + A2*sin(2πf2*t + φ2) + ...`

**Ưu điểm**:
- Xử lý được non-uniform sampling
- Có thể constrain frequencies dựa trên vật lý
- Tốt cho dao động phức tạp (nhiều harmonics)

**Nhược điểm**:
- Chậm hơn FFT
- Cần initial guess tốt

**Khi nào dùng**: Dao động có nhiều tần số (VD: guitar string, complex vibrations)

```python
t_new, v_new, params = reconstructor.method2_harmonic_fit(target_fs=100.0, n_harmonics=3)

# Xem fitted parameters
print("Fitted frequencies:")
for h in params['harmonics']:
    print(f"  - {h['frequency_Hz']:.2f} Hz, amplitude {h['amplitude']:.3f}")
```

### Method 3: Physics-Based (Damped Oscillation) 🔬 ⭐ KHUYẾN NGHỊ

**Ý tưởng**: Dùng mô hình vật lý cụ thể.

Model: `y(t) = A * exp(-γt) * sin(ωt + φ) + y0`

Phù hợp cho:
- Con lắc dao động tắt dần
- Spring-mass-damper systems
- Vibration decay

**Ưu điểm**:
- **Tốt nhất** cho dao động cơ học
- Cho ra các tham số vật lý (damping, frequency, Q-factor)
- Xử lý tốt cả undersampling nặng

**Nhược điểm**:
- Chỉ áp dụng cho một loại dao động cụ thể
- Cần model phù hợp với hiện tượng

**Khi nào dùng**: Dao động tắt dần (pendulum, spring, etc.)

```python
t_new, v_new, params = reconstructor.method3_physics_damped(target_fs=100.0)

# Xem physics parameters
print(f"Frequency: {params['frequency_Hz']:.2f} Hz")
print(f"Damping coefficient: {params['damping_coef']:.4f}")
print(f"Quality factor: {params['quality_factor']:.1f}")
print(f"Amplitude: {params['amplitude']:.3f}")
```

## Cách Sử Dụng

### Bước 1: Load dữ liệu từ CSV

```python
import pandas as pd
import numpy as np
from data_reconstruction import OscillationReconstructor

# Load raw data
df = pd.read_csv('recordings_upsampled/sensor_C_raw_20251107_121158.csv')
timestamps = df['time_s'].values
values = df['Accelerationx'].values  # Hoặc tên measurement của bạn

print(f"Original data: {len(timestamps)} points")
print(f"Sampling rate: ~{1/np.mean(np.diff(timestamps)):.1f} Hz")
```

### Bước 2: Tạo reconstructor

```python
reconstructor = OscillationReconstructor(timestamps, values)
```

### Bước 3: Thử các methods

```python
# Method 1: FFT
t1, v1 = reconstructor.method1_fft_based(target_fs=100.0)

# Method 2: Harmonic fit
t2, v2, params2 = reconstructor.method2_harmonic_fit(target_fs=100.0, n_harmonics=3)

# Method 3: Physics (TỐT NHẤT cho dao động cơ học)
t3, v3, params3 = reconstructor.method3_physics_damped(target_fs=100.0)
```

### Bước 4: So sánh và chọn method tốt nhất

```python
# Compare all methods visually
fig = reconstructor.compare_methods(target_fs=100.0)
plt.savefig('reconstruction_comparison.png', dpi=150)
plt.show()
```

### Bước 5: Lưu kết quả

```python
# Lưu reconstructed data
df_new = pd.DataFrame({
    'time_s': t3,
    'value_reconstructed': v3
})
df_new.to_csv('data_reconstructed_100Hz.csv', index=False)

print(f"Reconstructed: {len(t3)} points @ {100} Hz")
print(f"Original: {len(timestamps)} points @ ~{1/np.mean(np.diff(timestamps)):.1f} Hz")
```

## Example Workflow Hoàn Chỉnh

```python
#!/usr/bin/env python
"""
Workflow: Reconstruct oscillation from undersampled sensor data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_reconstruction import OscillationReconstructor

# 1. Load data
print("Loading data...")
df = pd.read_csv('recordings_upsampled/sensor_C_raw_20251107_121158.csv')
t_orig = df['time_s'].values
v_orig = df.iloc[:, 1].values  # Column 1 is the measurement

print(f"Loaded {len(t_orig)} points")
print(f"Time range: {t_orig[0]:.2f} - {t_orig[-1]:.2f} seconds")
print(f"Avg sampling rate: {1/np.mean(np.diff(t_orig)):.2f} Hz")

# 2. Create reconstructor
reconstructor = OscillationReconstructor(t_orig, v_orig)

# 3. Reconstruct với physics-based method
print("\nReconstructing with damped oscillation model...")
t_recon, v_recon, params = reconstructor.method3_physics_damped(target_fs=100.0)

# 4. Print physics parameters
print("\nFitted Physics Parameters:")
print(f"  Oscillation frequency: {params['frequency_Hz']:.2f} Hz")
print(f"  Damping coefficient: {params['damping_coef']:.4f}")
print(f"  Quality factor Q: {params['quality_factor']:.1f}")
print(f"  Amplitude: {params['amplitude']:.3f}")
print(f"  Phase: {params['phase_rad']:.3f} rad")

# 5. Visualize
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Original vs reconstructed
ax1.plot(t_orig, v_orig, 'o', label='Original (undersampled)', markersize=8, alpha=0.6)
ax1.plot(t_recon, v_recon, '-', label='Reconstructed (100 Hz)', linewidth=1.5, alpha=0.8)
ax1.set_xlabel('Time [s]')
ax1.set_ylabel('Value')
ax1.set_title('Reconstruction Result')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Zoom vào 2 giây đầu
ax2.plot(t_orig[t_orig <= 2], v_orig[t_orig <= 2], 'o', label='Original', markersize=10, alpha=0.6)
mask = t_recon <= 2
ax2.plot(t_recon[mask], v_recon[mask], '-', label='Reconstructed', linewidth=2, alpha=0.8)
ax2.set_xlabel('Time [s]')
ax2.set_ylabel('Value')
ax2.set_title('Zoomed View (first 2 seconds)')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('reconstruction_result.png', dpi=150)
print("\nSaved plot: reconstruction_result.png")
plt.show()

# 6. Save reconstructed data
df_recon = pd.DataFrame({
    'time_s': t_recon,
    'value': v_recon
})
df_recon.to_csv('data_reconstructed_100Hz.csv', index=False)
print(f"Saved: data_reconstructed_100Hz.csv ({len(t_recon)} points)")
```

## Giới Hạn và Cảnh Báo

### ⚠️ Không phải "phép màu"

Reconstruction **KHÔNG THỂ** phục hồi 100% dữ liệu đã mất. Nó chỉ **ước lượng** dựa trên:
- Pattern trong dữ liệu có sẵn
- Giả định về mô hình vật lý

### ⚠️ Khi nào KHÔNG nên dùng

1. **Aliasing quá nặng**: Tần số dao động >> sampling rate
   - VD: 20 Hz oscillation với 8 Hz sampling → Hoàn toàn sai

2. **Dao động không đều, random**:
   - Không có pattern → Không fit được model

3. **Transients, shocks**:
   - Các hiện tượng đột ngột, không tuần hoàn

4. **Yêu cầu độ chính xác tuyệt đối**:
   - Nếu cần chính xác 100% → Phải tăng sampling rate hardware

### ✅ Khi nào NÊN dùng

1. **Dao động gần tuần hoàn**: Spring, pendulum, vibrations
2. **Có mô hình vật lý**: Biết hệ thống tuân theo equation nào
3. **Chỉ cần ước lượng**: Không cần chính xác tuyệt đối
4. **Post-processing analysis**: Visualization, FFT, filtering

## So Sánh

| Phương pháp | Tốc độ | Độ chính xác | Yêu cầu | Phù hợp |
|-------------|--------|--------------|---------|---------|
| PCHIP (hiện tại) | ⚡⚡⚡ Rất nhanh | ❌ Không tái tạo dao động | Không | Smooth curve |
| FFT-based | ⚡⚡ Nhanh | ⚠️ Trung bình | SR > Nyquist | Periodic signals |
| Harmonic fit | ⚡ Chậm | ✅ Tốt | Initial guess | Complex oscillations |
| Physics damped | ⚡ Chậm | ✅✅ Rất tốt | Đúng model | Mechanical oscillations |

## Kết Luận

### Giải pháp tốt nhất:

1. **Hardware**: Tăng sampling rate (nếu có thể) - **Không khả thi với PASCO BLE**
2. **Software**: Dùng **Method 3 (Physics-based)** cho dao động cơ học
3. **Hybrid**: Dùng PCHIP cho smooth visualization, Physics-based cho analysis

### Workflow khuyến nghị:

```
1. Thu thập dữ liệu raw (8 Hz) → Auto-save
2. PCHIP upsampling (50 Hz) → Real-time visualization
3. Physics reconstruction (100 Hz) → Post-analysis
4. So sánh và chọn phương pháp phù hợp
```

### Test ngay:

```bash
# 1. Pull code
git pull origin claude/setup-venv-pasco-011CUsnqbc5s6Pw4Gd4gHdNn

# 2. Test với dữ liệu mẫu
venv-pasco/bin/python data_reconstruction.py

# 3. Test với dữ liệu thực của bạn
venv-pasco/bin/python -c "
import pandas as pd
from data_reconstruction import OscillationReconstructor
df = pd.read_csv('recordings_upsampled/sensor_C_raw_*.csv')
recon = OscillationReconstructor(df['time_s'].values, df.iloc[:, 1].values)
recon.compare_methods(target_fs=100.0)
"
```

Hãy thử và cho tôi biết kết quả! 🚀
