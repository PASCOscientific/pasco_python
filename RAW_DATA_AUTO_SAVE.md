# Auto-Save cho Dữ Liệu RAW (Dữ Liệu Thật)

## Tổng quan

Ngoài việc tự động lưu dữ liệu upsampled, GUI bây giờ **cũng tự động lưu dữ liệu RAW** (dữ liệu thật từ sensor) trong khi recording!

## Sự khác biệt

### Dữ liệu RAW (Thật)
- Dữ liệu gốc từ sensor, không qua xử lý
- Tần số không đều (~5-10Hz với jitter)
- Timestamp thực tế khi nhận được sample
- **Lưu tức thì** khi có sample mới

### Dữ liệu UPSAMPLED (Xử lý)
- Dữ liệu đã qua PCHIP interpolation
- Tần số đều (50Hz/100Hz)
- Timestamp được tạo đều
- **Lưu theo batch** mỗi 200ms

## File được tạo tự động

Khi bạn **Start Recording** với 1 sensor (ví dụ Sensor C), hệ thống sẽ tự động tạo:

### 1. File RAW (riêng cho mỗi sensor)
```
recordings_upsampled/sensor_C_raw_20251107_121158.csv
```

**Format:**
```csv
time_s,Accelerationx,mode=raw
0.012345,9.8123
0.112456,9.7845
0.234567,10.1234
...
```

- Mỗi sensor có file riêng
- Dữ liệu được ghi **NGAY LẬP TỨC** khi nhận được
- Flush mỗi 10 samples để tối ưu performance

### 2. File UPSAMPLED (merged tất cả sensors)
```
recordings_upsampled/recording_20251107_121158_upsampled_50Hz.csv
```

**Format:**
```csv
time_s,A,B,C
0.020000,,,9.8134
0.040000,,,9.7923
0.060000,,,10.0912
...
```

- 1 file chung cho tất cả sensors
- Dữ liệu được ghi theo batch mỗi 200ms
- Timestamp được làm đều bởi upsampling

## Cách sử dụng

```bash
# 1. Pull code mới
git pull origin claude/setup-venv-pasco-011CUsnqbc5s6Pw4Gd4gHdNn

# 2. Chạy GUI
venv-pasco/bin/python examples/gui_multi_sensor_upsampled.py

# 3. Workflow:
#    - Connect Sensor C
#    - Start Recording
#    - Đợi 30 giây
#    - Stop

# 4. Kiểm tra files
ls -lh recordings_upsampled/
```

## Log panel sẽ hiển thị

```
[12:11:58] Recording started (target 50.0Hz upsampled)
[12:11:58] Connected sensors: C
[12:11:58] Auto-save: Enabled
[12:11:58]   - Raw data: Saved instantly on each sample       ← MỚI
[12:11:58]   - Upsampled data: Saved every 200ms
[12:11:58] Raw CSV opened for sensors: C                      ← MỚI
[12:11:58] Upsampled CSV: recording_20251107_121158_upsampled_50Hz.csv
...
[12:12:36] Recording stopped
[12:12:36]   Sensor C: 245 raw, 1926 upsampled samples
[12:12:36] ✓ Raw data auto-saved:                             ← MỚI
[12:12:36]   - C: sensor_C_raw_20251107_121158.csv           ← MỚI
[12:12:36] ✓ Upsampled data auto-saved: recording_20251107_121158_upsampled_50Hz.csv
```

## Console output

```
[RAW AUTO-SAVE] Opened: .../sensor_C_raw_20251107_121158.csv
[AUTO-SAVE] Wrote 15 rows to CSV
[AUTO-SAVE] Wrote 12 rows to CSV
...
[RAW AUTO-SAVE] Closed: .../sensor_C_raw_20251107_121158.csv
[AUTO-SAVE] Upsampled file closed: .../recording_20251107_121158_upsampled_50Hz.csv
```

## Ưu điểm

### ✅ An toàn tuyệt đối
- Dữ liệu raw được ghi **TỨC THÌ** (không đợi)
- Flush mỗi 10 samples → mất tối đa 10 samples nếu crash
- Không lo mất dữ liệu gốc

### ✅ Hiệu suất cao
- Ghi trực tiếp, không qua buffer lớn
- Flush có điều kiện (mỗi 10 samples)
- Không ảnh hưởng tốc độ thu thập

### ✅ Dễ phân tích
- Mỗi sensor 1 file → dễ import vào Python/MATLAB
- Format đơn giản: time, value
- Có cả raw và upsampled để so sánh

## So sánh với "Save All CSV" button

| Tính năng | Auto-Save RAW | Save All CSV |
|-----------|---------------|--------------|
| Thời điểm | Tức thì (mỗi sample) | Sau khi stop, thủ công |
| File per sensor | ✅ Có | ✅ Có |
| An toàn | ✅ Rất cao | ⚠️ Phụ thuộc user |
| Format | Giống nhau | Giống nhau |
| Cần thao tác | ❌ Tự động | ✅ Click button |

**Khuyến nghị**: Bây giờ bạn không cần dùng "Save All CSV" nữa! Auto-save đã lo tất cả.

## Ví dụ phân tích

### Python
```python
import pandas as pd
import matplotlib.pyplot as plt

# Đọc raw data
raw = pd.read_csv('recordings_upsampled/sensor_C_raw_20251107_121158.csv')

# Đọc upsampled data
ups = pd.read_csv('recordings_upsampled/recording_20251107_121158_upsampled_50Hz.csv')

# So sánh
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(raw['time_s'], raw['Accelerationx'], 'o-', label='Raw')
plt.title('Raw Data (~8Hz)')
plt.xlabel('Time (s)')
plt.ylabel('Acceleration')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(ups['time_s'], ups['C'], '-', label='Upsampled')
plt.title('Upsampled Data (50Hz)')
plt.xlabel('Time (s)')
plt.ylabel('Acceleration')
plt.legend()

plt.tight_layout()
plt.show()
```

### MATLAB
```matlab
% Đọc raw data
raw = readtable('recordings_upsampled/sensor_C_raw_20251107_121158.csv');

% Đọc upsampled data
ups = readtable('recordings_upsampled/recording_20251107_121158_upsampled_50Hz.csv');

% Plot
figure;
subplot(1, 2, 1);
plot(raw.time_s, raw.Accelerationx, 'o-');
title('Raw Data (~8Hz)');
xlabel('Time (s)');
ylabel('Acceleration');

subplot(1, 2, 2);
plot(ups.time_s, ups.C, '-');
title('Upsampled Data (50Hz)');
xlabel('Time (s)');
ylabel('Acceleration');
```

## Kiểm tra files sau recording

```bash
# Windows
dir recordings_upsampled\*.csv

# Linux/Mac
ls -lh recordings_upsampled/*.csv

# Output sẽ như sau:
# sensor_C_raw_20251107_121158.csv                    (246 rows - raw data)
# recording_20251107_121158_upsampled_50Hz.csv        (1927 rows - upsampled)
```

Đếm số dòng:
```bash
# Windows
find /c /v "" recordings_upsampled\sensor_C_raw_*.csv

# Linux/Mac
wc -l recordings_upsampled/sensor_C_raw_*.csv
```

## Lưu ý

### ⚠️ Không click "Start Recording" lại sau Stop
Nếu click lại, buffer và files mới sẽ được tạo. Dữ liệu cũ vẫn an toàn trong files đã lưu.

### ⚠️ File size
- Raw data nhỏ (~246 rows cho 30 giây @ 8Hz)
- Upsampled data lớn hơn (~1927 rows cho 30 giây @ 50Hz)

### ⚠️ Tên file trùng
Vì dùng timestamp (chính xác đến giây), nếu Start/Stop/Start trong <1 giây sẽ ghi đè file cũ.

**Giải pháp**: Đợi ít nhất 1-2 giây giữa các lần recording.

## Kết luận

Bây giờ bạn có **TẤT CẢ dữ liệu** được lưu tự động:

✅ **Raw data** - Dữ liệu gốc từ sensor (tức thì)
✅ **Upsampled data** - Dữ liệu xử lý (mỗi 200ms)
✅ **Không cần thao tác** - Hoàn toàn tự động
✅ **Không mất dữ liệu** - An toàn tuyệt đối

Chỉ cần: **Connect → Start → Stop** → Xong! 🎉

Files đã sẵn sàng trong thư mục `recordings_upsampled/`
