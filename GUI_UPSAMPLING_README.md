# GUI Multi-Sensor với Real-time Upsampling

## 🎯 Tổng quan

File `examples/gui_multi_sensor_upsampled.py` là phiên bản cải tiến của GUI PASCO với **upsampling real-time**, giải quyết vấn đề tần số không ổn định do Bluetooth.

### Vấn đề cũ
- Tần số lấy mẫu qua Bluetooth không ổn định (~5-10Hz, có jitter)
- Hiển thị giật, không mượt
- FFT không chính xác do tần số không đều

### Giải pháp mới
- **Dual-buffer system**: Raw data + Upsampled data
- **PCHIP interpolation**: Nội suy trơn tru, giữ tính vật lý
- **Tần số ổn định**: 50Hz, 100Hz, hoặc 200Hz
- **Real-time processing**: Upsampling diễn ra liên tục trong background

---

## 🚀 Cài đặt và chạy

### Yêu cầu hệ thống

**✅ Trên máy local (Windows/Mac/Linux với GUI):**

1. Python 3.11
2. Tkinter (system package)
3. Dependencies từ venv-pasco

**Cài đặt tkinter:**

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS (thường đã có sẵn)
# Nếu không có, cài Python từ python.org (đã bao gồm tkinter)

# Windows
# Python từ python.org đã bao gồm tkinter
```

### Chạy GUI

```bash
# Activate virtual environment
source venv-pasco/bin/activate

# Hoặc dùng trực tiếp
venv-pasco/bin/python examples/gui_multi_sensor_upsampled.py
```

---

## 📊 Tính năng

### 1. **Dual-Buffer System**

```
┌─────────────────┐
│  Sensor (BLE)   │
│   ~5-10 Hz      │ ← Tần số không ổn định do Bluetooth
└────────┬────────┘
         │
         ▼
   ┌──────────────┐
   │  RAW BUFFER  │
   │ (Timestamp    │
   │  thực, jitter)│
   └──────┬───────┘
          │
          │ PCHIP Interpolation
          │ (mỗi 200ms)
          ▼
   ┌──────────────┐
   │ UPSAMPLED    │
   │   BUFFER     │
   │ (50Hz/100Hz  │
   │  ổn định)    │
   └──────┬───────┘
          │
          ▼
     ┌────────┐
     │  GUI   │ ← Hiển thị mượt mà
     └────────┘
```

### 2. **PCHIP Interpolation**

- **Piecewise Cubic Hermite Interpolating Polynomial**
- Giữ tính đơn điệu của dữ liệu
- Không tạo overshoot (vượt qua giá trị gốc)
- Phù hợp với sensor data vật lý

### 3. **Tần số upsampling linh hoạt**

Chọn từ toolbar:
- **20 Hz**: Nhẹ, tiết kiệm CPU
- **50 Hz**: Khuyến nghị cho hầu hết ứng dụng
- **100 Hz**: Smooth hơn, phù hợp cầu dao động
- **200 Hz**: Maximum smoothness

### 4. **Statistics Real-time**

Mỗi sensor hiển thị:
- `Raw: X` - Số mẫu trong raw buffer
- `Up: Y` - Số mẫu trong upsampled buffer
- `~Z Hz` - Tần số thực tế ước lượng

Ví dụ: `Raw:45 Up:250 ~8.3Hz`
- Thu được 45 mẫu gốc
- Upsampled thành 250 mẫu (tăng ~5.5x)
- Tần số thực qua Bluetooth: ~8.3Hz

### 5. **Dual CSV Export**

Khi save, tạo 2 files cho mỗi sensor:
- `sensor_A_raw_YYYYMMDD_HHMMSS.csv` - Dữ liệu gốc
- `sensor_A_upsampled_50Hz_YYYYMMDD_HHMMSS.csv` - Dữ liệu upsampled

---

## 🎮 Hướng dẫn sử dụng

### Bước 1: Kết nối sensors

1. Nhập ID sensor (6 chữ số, ví dụ: `966-489`)
2. Click **Connect**
3. Chọn measurement (ví dụ: `Accelerationx`)
4. Lặp lại cho sensor B, C nếu có

### Bước 2: Cấu hình upsampling

1. Chọn tần số upsampling từ dropdown **Upsample Fs**
2. Khuyến nghị: **50 Hz** cho cầu dao động
3. Cao hơn nếu cần smooth hơn (nhưng tốn CPU)

### Bước 3: Bắt đầu recording

1. Click **Start Recording**
2. GUI sẽ:
   - Thu thập dữ liệu raw (~5-10Hz qua Bluetooth)
   - Tự động upsample lên tần số đã chọn (50Hz)
   - Hiển thị real-time với dữ liệu upsampled
   - Lưu auto vào CSV

### Bước 4: Quan sát

- **Time Domain tab**: Xem dạng sóng acceleration (upsampled, mượt)
- **Frequency (FFT) tab**: Phân tích tần số
- **Stats**: Theo dõi `Raw/Up/~Hz` để kiểm tra hiệu suất

### Bước 5: Dừng và lưu

1. Click **Stop** khi xong
2. Click **Save All CSV** để lưu cả raw và upsampled
3. Chọn thư mục output

---

## ⚙️ Cấu hình nâng cao

### Thay đổi default sensor IDs

Edit dòng 147 trong code:

```python
self.default_ids = ['966-489', '946-449', '964-462']  # Thay bằng ID của bạn
```

### Tùy chỉnh tần số upsampling

Edit dòng 134:

```python
self.upsample_fs_choices = [20, 50, 100, 200, 400]  # Thêm/bớt tùy chọn
self.upsample_fs = 50.0  # Tần số mặc định
```

### Thay đổi window hiển thị

Edit dòng 140:

```python
self.window_s = 30.0  # Hiển thị 30 giây gần nhất
```

### Tần số upsampling

Edit dòng 179:

```python
self.upsample_interval_ms = 200  # Upsample mỗi 200ms
```

Giảm xuống 100ms nếu muốn upsampling thường xuyên hơn (nhưng tốn CPU).

### Buffer size

Edit trong `SensorClient.__init__()`:

```python
self.raw_data = deque(maxlen=500)      # Raw buffer (500 mẫu)
self.upsampled_data = deque(maxlen=3000)  # Upsampled buffer
```

---

## 📈 So sánh với GUI gốc

| Tính năng | GUI gốc | GUI Upsampled |
|-----------|---------|---------------|
| **Tần số hiển thị** | ~10Hz (không ổn định) | 50-200Hz (ổn định) |
| **Độ mượt** | Giật, có jitter | Mượt mà |
| **Interpolation** | Linear (2 điểm cuối) | PCHIP (toàn bộ window) |
| **Buffer** | Single buffer | Dual buffer (raw + upsampled) |
| **CSV output** | Raw only | Raw + Upsampled |
| **Statistics** | Không | Real-time (Raw/Up/Freq) |
| **FFT chính xác** | Kém (do tần số không đều) | Tốt (tần số ổn định) |

---

## 🔬 Kỹ thuật implementation

### Class SensorClient

```python
class SensorClient:
    def __init__(self, name, color, target_fs=50.0):
        # Dual buffers
        self.raw_data = deque(maxlen=500)        # Dữ liệu gốc
        self.upsampled_data = deque(maxlen=3000) # Upsampled

        self.target_fs = target_fs  # Tần số mục tiêu

    def add_sample(self, timestamp, value):
        """Thêm sample vào raw buffer"""
        self.raw_data.append((timestamp, value))

    def upsample_recent(self, current_time):
        """Upsample dữ liệu gần đây bằng PCHIP"""
        # Lấy dữ liệu trong window 5s gần nhất
        # Áp dụng PCHIP interpolation
        # Thêm vào upsampled_data buffer
```

### Workflow

```
Main Loop (10Hz):
├─ _tick() → Thu thập raw data từ sensors
│
Upsampling Loop (5Hz - mỗi 200ms):
├─ _upsample_all() → PCHIP interpolation cho mọi sensor
│  └─ sensor.upsample_recent()
│     ├─ Lấy dữ liệu raw trong window 5s
│     ├─ Tạo PCHIP interpolator
│     ├─ Generate uniform timestamps (50Hz/100Hz)
│     └─ Thêm vào upsampled_data
│
Plot Loop (10Hz - mỗi 100ms):
└─ _refresh_plots() → Vẽ từ upsampled_data
   ├─ _draw_time_plot() → Time domain
   └─ _draw_fft_plot() → FFT
```

### PCHIP Interpolation Code

```python
from scipy import interpolate

# Extract data
timestamps = np.array([t for t, _ in recent_raw])
values = np.array([v for _, v in recent_raw])

# Create PCHIP interpolator
interpolator = interpolate.PchipInterpolator(timestamps, values)

# Generate uniform timestamps
uniform_timestamps = np.linspace(t_start, t_end, n_points)

# Interpolate
upsampled_values = interpolator(uniform_timestamps)
```

---

## ⚠️ Lưu ý quan trọng

### 1. **Upsampling không tạo thông tin mới**

Dữ liệu upsampled chỉ là **ước lượng** giá trị giữa các điểm đo thực.

❌ **KHÔNG dùng để**:
- Phát hiện sự kiện rất ngắn (<100ms)
- Phân tích tần số cao hơn Nyquist của raw data

✅ **TỐT để**:
- Hiển thị mượt mà
- Đồng bộ với tín hiệu khác
- Cải thiện FFT bằng tần số đều

### 2. **CPU Usage**

Upsampling tốn CPU. Nếu máy yếu:
- Giảm tần số upsampling (20Hz thay vì 100Hz)
- Tăng `upsample_interval_ms` (300ms thay vì 200ms)
- Tắt FFT khi không cần

### 3. **Tần số Nyquist**

Với raw data ~8Hz, chỉ phát hiện được tần số đến **4Hz** (Nyquist).

Upsampling lên 100Hz **KHÔNG** giúp phát hiện tần số >4Hz!

### 4. **Latency**

Upsampling cần ít nhất 4 điểm → có độ trễ ~0.5s khi bắt đầu recording.

---

## 🐛 Troubleshooting

### GUI không mở được

**Lỗi: `ModuleNotFoundError: No module named 'tkinter'`**

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS - cài Python từ python.org
# Windows - đã có sẵn
```

### Upsampling không hoạt động

**Kiểm tra:**
1. `scipy` đã được cài: `pip list | grep scipy`
2. Raw data buffer có ít nhất 4 điểm
3. Check stats: `Raw:X` phải > 4

### Hiển thị vẫn giật

**Nguyên nhân:**
- Bluetooth quá yếu
- Sensor ID sai
- Tần số upsampling quá thấp

**Giải pháp:**
- Kiểm tra kết nối Bluetooth
- Tăng tần số upsampling lên 100Hz
- Giảm `plot_interval_ms` xuống 50ms

### CSV bị thiếu dữ liệu

**Nguyên nhân:** CSV auto-save chưa được implement đầy đủ trong phiên bản này.

**Giải pháp:** Dùng **Save All CSV** button khi stop recording.

---

## 📚 Tài liệu liên quan

- [UPSAMPLING_GUIDE.md](../UPSAMPLING_GUIDE.md) - Chi tiết về upsampling
- [README.md](../README.md) - PASCO Python API
- [data_upsampling.py](../data_upsampling.py) - Module upsampling độc lập

---

## 🎓 Ví dụ use cases

### 1. Đo dao động cầu

```
Cấu hình:
- 3 sensors tại 3 vị trí trên cầu
- Upsampling: 50Hz
- Window: 30s
- Measurement: Accelerationx

Kết quả:
- Tần số dao động: 2.3Hz (từ FFT)
- Biên độ max: 0.15 m/s²
- Hiển thị mượt, dễ quan sát
```

### 2. Phân tích진동 (vibration)

```
Cấu hình:
- Upsampling: 100Hz
- FFT enabled
- Performance mode: OFF

Phân tích:
- Dominant frequency từ FFT tab
- Waveform pattern từ Time Domain
- Export CSV cho MATLAB/Python analysis
```

---

## 🔄 Workflow khuyến nghị

```
1. Chuẩn bị
   ├─ Kết nối sensors
   ├─ Kiểm tra measurements
   └─ Chọn upsample frequency

2. Test run
   ├─ Start recording 10s
   ├─ Check stats (Raw/Up/Freq)
   └─ Stop và kiểm tra plots

3. Production run
   ├─ Start recording
   ├─ Thu thập dữ liệu (30s - 5 phút)
   ├─ Quan sát FFT real-time
   └─ Stop

4. Export và phân tích
   ├─ Save All CSV
   ├─ Mở upsampled CSV với MATLAB/Excel
   └─ Phân tích tần số, biên độ
```

---

**Tác giả**: Claude AI Assistant
**Ngày tạo**: 2025-11-07
**Version**: 1.0
**License**: Theo PASCO Python package
