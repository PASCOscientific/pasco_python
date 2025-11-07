# Hướng dẫn Upsampling dữ liệu PASCO Sensors

## 🎯 Mục đích

Tăng tần số dữ liệu từ PASCO sensors từ ~5-10Hz lên 50Hz, 100Hz hoặc cao hơn bằng các phương pháp nội suy (interpolation).

## ⚠️ Lưu ý quan trọng

**Upsampling KHÔNG tạo ra thông tin mới!** Nó chỉ ước lượng giá trị giữa các điểm đo thực tế.

- ✅ **Tốt cho**: Visualization, làm mượt dữ liệu, đồng bộ với tín hiệu khác
- ❌ **KHÔNG tốt cho**: Phân tích tần số cao, phát hiện sự kiện ngắn hạn

## 📦 Cài đặt

Tất cả dependencies đã được cài trong `venv-pasco`:

```bash
# Kích hoạt virtual environment
source venv-pasco/bin/activate

# Hoặc chạy trực tiếp
venv-pasco/bin/python your_script.py
```

**Packages đã cài:**
- `pasco` (thư viện PASCO)
- `numpy` (tính toán)
- `scipy` (nội suy)
- `matplotlib` (visualization - nếu cần)

## 🚀 Cách sử dụng

### 1. Demo mode (không cần sensor)

```bash
venv-pasco/bin/python collect_and_upsample.py --demo
```

Tạo dữ liệu giả lập và upsampling để test.

### 2. Với sensor thật

**Bước 1: Kết nối và thu thập dữ liệu**

```python
from collect_and_upsample import main_workflow

main_workflow(
    sensor_id='123-456',           # ID sensor của bạn (6 chữ số)
    measurements=['Temperature'],   # Chọn measurement(s)
    duration=10,                    # Thời gian thu (giây)
    target_freq=50,                 # Tần số upsampling (Hz)
    upsample_method='pchip'         # Phương pháp nội suy
)
```

**Bước 2: Scan sensor nếu không biết ID**

```python
main_workflow(
    sensor_id=None,                # Sẽ scan và cho chọn
    measurements=['Temperature'],
    duration=10,
    target_freq=50
)
```

### 3. Chỉ upsampling dữ liệu có sẵn

Nếu bạn đã có dữ liệu trong file CSV:

```python
from data_upsampling import upsample_from_pasco_data
import csv

# Đọc dữ liệu
data = []
with open('your_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append({
            'timestamp': float(row['timestamp']),
            'Temperature': float(row['Temperature'])
        })

# Upsampling
upsampled = upsample_from_pasco_data(
    data,
    target_freq=50,
    measurement_key='Temperature'
)

# Lưu kết quả
with open('upsampled_data.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['timestamp', 'Temperature'])
    writer.writeheader()
    writer.writerows(upsampled)
```

## 🔬 Các phương pháp nội suy

### 1. **LINEAR** (Tuyến tính)
```python
upsample_method='linear'
```
- ⚡ **Nhanh nhất**
- ✅ Đơn giản, ổn định
- ❌ Có góc nhọn tại các điểm mẫu
- **Dùng khi**: Cần tốc độ, dữ liệu không quá dao động

### 2. **CUBIC** (Đường cong bậc 3)
```python
upsample_method='cubic'
```
- 📈 **Trơn tru nhất**
- ✅ Đường cong mượt mà
- ❌ Có thể overshoot (vượt qua giá trị gốc)
- **Dùng khi**: Tín hiệu liên tục, smooth signals

### 3. **PCHIP** (Piecewise Cubic Hermite) - **Khuyến nghị**
```python
upsample_method='pchip'
```
- ⭐ **Tốt nhất cho sensor data**
- ✅ Trơn, giữ tính đơn điệu
- ✅ Không overshoot
- ✅ Phù hợp với dữ liệu vật lý
- **Dùng khi**: Temperature, Pressure, Force, v.v.

## 📊 Kết quả demo

**Dữ liệu gốc** (8Hz, 80 mẫu):
```
timestamp,Temperature
0.0,23.045
0.126,23.573
0.253,24.689
...
```

**Upsampled** (50Hz, 500 mẫu):
```
timestamp,Temperature
0.0,23.045
0.020,23.092
0.040,23.156
0.060,23.235
...
```

**Tăng 6.2x số lượng mẫu!**

## 📁 Cấu trúc output

```
data_output/
├── 20251107_032429/
│   ├── original_data.csv          # Dữ liệu gốc
│   ├── Temperature_pchip_50Hz.csv # Upsampled Temperature
│   └── Force_pchip_50Hz.csv       # Upsampled Force (nếu có)
└── demo_20251107_032429/
    ├── demo_original.csv
    └── demo_upsampled_50Hz.csv
```

## 🔧 Tùy chỉnh nâng cao

### So sánh các phương pháp

```python
from data_upsampling import DataUpsampler

# Tạo upsampler
upsampler = DataUpsampler(original_data, original_freq=8)

# So sánh tất cả phương pháp
results = upsampler.compare_methods(target_freq=50)

# Kết quả: dict với keys: 'linear', 'cubic', 'pchip'
for method, result in results.items():
    print(f"{method}: {result['new_samples']} mẫu")
```

### Thu thập nhiều measurements cùng lúc

```python
main_workflow(
    sensor_id='123-456',
    measurements=['Temperature', 'Pressure', 'Humidity'],
    duration=30,
    target_freq=100
)
```

### Tùy chỉnh collector

```python
from collect_and_upsample import PASCODataCollector

collector = PASCODataCollector()
collector.connect('123-456')

# Thu thập custom
data = collector.collect_data(
    measurements=['Temperature'],
    duration=60,
    verbose=True
)

collector.disconnect()
```

## 📈 Ví dụ thực tế

### 1. Upsampling Temperature sensor

```python
from collect_and_upsample import main_workflow

# Thu 30s, upsampling lên 100Hz
main_workflow(
    sensor_id='055-808',
    measurements=['Temperature'],
    duration=30,
    target_freq=100,
    upsample_method='pchip'
)
```

### 2. Nhiều sensors cùng lúc

```python
# Cần kết nối từng sensor riêng
from collect_and_upsample import PASCODataCollector
from data_upsampling import upsample_from_pasco_data

# Sensor 1: Temperature
temp_collector = PASCODataCollector()
temp_collector.connect('123-456')
temp_data = temp_collector.collect_data(['Temperature'], duration=10)
temp_collector.disconnect()

# Sensor 2: Force
force_collector = PASCODataCollector()
force_collector.connect('789-012')
force_data = force_collector.collect_data(['Force'], duration=10)
force_collector.disconnect()

# Upsampling
temp_upsampled = upsample_from_pasco_data(temp_data, 50, 'Temperature')
force_upsampled = upsample_from_pasco_data(force_data, 50, 'Force')
```

## ❓ FAQ

### Q: Tần số upsampling tối đa là bao nhiêu?
**A:** Không có giới hạn kỹ thuật, nhưng:
- 5-10x tần số gốc là hợp lý (8Hz → 50-80Hz)
- Quá cao (>100x) không có ý nghĩa vật lý

### Q: Upsampling có làm tăng độ chính xác không?
**A:** **KHÔNG**. Upsampling chỉ làm mượt dữ liệu, không tăng độ chính xác hay phát hiện được chi tiết mới.

### Q: Phương pháp nào tốt nhất?
**A:**
- **PCHIP** cho hầu hết sensor data (Temperature, Pressure, Force)
- **LINEAR** nếu cần tốc độ
- **CUBIC** nếu biết tín hiệu rất smooth

### Q: Upsampling có tốn nhiều thời gian không?
**A:** Rất nhanh! Upsampling 80 mẫu → 500 mẫu chỉ mất ~0.4ms.

### Q: Có thể downsample (giảm tần số) không?
**A:** Có, nhưng tool này chưa hỗ trợ. Downsampling đơn giản hơn: chỉ cần lấy mẫu theo bước nhảy.

## 🛠️ Troubleshooting

### Lỗi: "target_freq <= original_freq"
- Tần số mục tiêu phải cao hơn tần số gốc
- Kiểm tra tần số thu thập thực tế

### Lỗi: "Not enough data points"
- Cần ít nhất 4 điểm để nội suy cubic/pchip
- Thu thập dữ liệu lâu hơn

### Upsampling không smooth
- Thử phương pháp 'cubic' hoặc 'pchip'
- Kiểm tra dữ liệu gốc có nhiễu quá không

## 📚 Tài liệu tham khảo

- [SciPy Interpolation](https://docs.scipy.org/doc/scipy/reference/interpolate.html)
- [PASCO Python API](README.md)
- [Upsampling vs Interpolation](https://en.wikipedia.org/wiki/Upsampling)

## 🎓 Lưu ý khoa học

1. **Định lý Nyquist-Shannon**: Để tái tạo tín hiệu tần số `f`, cần lấy mẫu ít nhất `2f`.
   - Nếu sensor có dao động 5Hz, cần lấy mẫu ≥10Hz
   - Upsampling không giúp phục hồi tín hiệu bị aliasing

2. **Overfitting**: Upsampling quá cao có thể tạo artifacts (giả tạo)

3. **Uncertainty**: Độ không chắc chắn của điểm nội suy cao hơn điểm đo thực

---

**Tác giả**: Claude AI Assistant
**Ngày tạo**: 2025-11-07
**Version**: 1.0
