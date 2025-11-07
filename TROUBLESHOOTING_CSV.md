# Hướng dẫn chẩn đoán lỗi file CSV rỗng

## Vấn đề
File CSV không có dữ liệu sau khi lưu (cả raw và upsampled đều rỗng).

## Các bước kiểm tra

### 1. Pull code mới nhất
```bash
git pull origin claude/setup-venv-pasco-011CUsnqbc5s6Pw4Gd4gHdNn
```

### 2. Chạy GUI với logging đầy đủ
```bash
cd /path/to/pasco_python
venv-pasco/bin/python examples/gui_multi_sensor_upsampled.py 2>&1 | tee debug_log.txt
```

### 3. Kết nối sensor

Sau khi click "Connect", kiểm tra trong **Log panel** bên trái:
- `[HH:MM:SS] Sensor A: connected` ✓
- Kiểm tra dropdown "Measurement" đã chọn đúng measurement (VD: "Acceleration X") chưa

### 4. Bắt đầu recording

Click "Start Recording" và kiểm tra Log panel:

**Phải thấy những dòng này:**
```
[HH:MM:SS] Sensor A config:
[HH:MM:SS]   - ID: 966-489
[HH:MM:SS]   - Measurement: Acceleration X (hoặc tên measurement khác)
[HH:MM:SS]   - Unit: m/s²
[HH:MM:SS] Recording started (target 50Hz upsampled)
[HH:MM:SS] Connected sensors: A
```

**⚠️ Nếu thấy dòng này = LỖI:**
```
[HH:MM:SS]   ⚠ WARNING: No measurement selected!
```
→ **NGUYÊN NHÂN**: Measurement chưa được chọn → dữ liệu không được đọc
→ **GIẢI PHÁP**: Chọn measurement từ dropdown trước khi Start Recording

### 5. Thu thập dữ liệu

**Trong vòng 5-10 giây**, bạn PHẢI thấy trong Log panel:
```
[HH:MM:SS] Sensor A: First sample received! Value=9.8123
[HH:MM:SS] Sensor A: 10 raw samples (latest=9.7845)
[HH:MM:SS] Sensor A: Upsampled! 0 → 15 points
[HH:MM:SS] Sensor A: 20 raw samples (latest=9.8234)
[HH:MM:SS] Sensor A: Upsampled! 15 → 45 points
```

**⚠️ Nếu KHÔNG thấy dòng "First sample received!":**

Kiểm tra terminal output (console) xem có lỗi không:
- `Sensor A: read_once() returned NoneType: None` → Sensor không trả về dữ liệu
- `Error reading sensor A: ...` → Có exception khi đọc sensor

### 6. Dừng recording

Click "Stop" và kiểm tra Log panel:
```
[HH:MM:SS] Recording stopped
[HH:MM:SS]   Sensor A: 100 raw, 500 upsampled samples
```

**⚠️ Nếu thấy "0 raw, 0 upsampled" = LỖI:**
→ Dữ liệu không được thu thập (quay lại bước 4-5)

### 7. Lưu CSV

Click "Save All CSV" và chọn thư mục. Kiểm tra:

**Trong Log panel:**
```
[HH:MM:SS] ✓ Saved raw: 100 rows → /path/sensor_A_raw_20250107_123456.csv
[HH:MM:SS] ✓ Saved upsampled: 500 rows → /path/sensor_A_upsampled_50Hz_20250107_123456.csv
```

**Trong terminal (console):**
```
[DEBUG] save_csv for sensor A:
  Mode: raw
  Buffer length: 100
  Buffer type: <class 'collections.deque'>
  Connected: True
  Selected measurement: Acceleration X
  Converted to list: 100 items
  First item: (0.012345, 9.8123)
  Last item: (10.567890, 9.7845)
  ✓ Wrote 100 rows to /path/sensor_A_raw_20250107_123456.csv

[DEBUG] save_csv for sensor A:
  Mode: upsampled
  Buffer length: 500
  ...
  ✓ Wrote 500 rows to /path/sensor_A_upsampled_50Hz_20250107_123456.csv
```

**⚠️ Nếu thấy "Buffer length: 0" = LỖI:**
→ Buffer rỗng → dữ liệu không được thu thập hoặc đã bị xóa

### 8. Kiểm tra file CSV

```bash
wc -l sensor_A_raw_*.csv
# Phải thấy: 101 sensor_A_raw_20250107_123456.csv (100 dòng data + 1 header)

head -5 sensor_A_raw_*.csv
# Phải thấy:
# time_s,Acceleration X,mode=raw
# 0.012345,9.8123
# 0.112456,9.7845
# ...
```

## Nguyên nhân thường gặp

### 1. Measurement chưa được chọn ⭐ THƯỜNG GẶP NHẤT
**Triệu chứng:**
- Log hiện: "WARNING: No measurement selected!"
- Không có dòng "First sample received!"
- Buffer length = 0 khi save

**Giải pháp:**
- SAU KHI connect sensor, BẮT BUỘC phải chọn measurement từ dropdown
- Đợi 1-2 giây sau khi chọn measurement
- Mới click "Start Recording"

### 2. Sensor không trả về dữ liệu
**Triệu chứng:**
- Log hiện: "read_once() returned NoneType: None"
- Không có dòng "First sample received!"

**Giải pháp:**
- Kiểm tra sensor có đang bật và có pin không
- Thử disconnect và connect lại
- Thử sensor khác

### 3. Exception khi đọc sensor
**Triệu chứng:**
- Log hiện: "Error reading sensor A: ..."
- Terminal có traceback

**Giải pháp:**
- Gửi full traceback để debug
- Kiểm tra version của pasco library

### 4. Data bị clear sau khi dừng
**Triệu chứng:**
- Lúc stop thấy "100 raw samples"
- Nhưng lúc save thấy "Buffer length: 0"

**Giải pháp:**
- Không click "Start Recording" lại sau khi stop (sẽ clear buffer)
- Save ngay sau khi stop

## Báo cáo lỗi

Nếu vẫn gặp lỗi, gửi cho tôi:

1. **Screenshot Log panel** sau khi:
   - Connect
   - Start Recording (đợi 10 giây)
   - Stop
   - Save CSV

2. **Terminal output** (file debug_log.txt) chứa tất cả debug messages

3. **Output của lệnh:**
```bash
ls -lh sensor_*.csv
wc -l sensor_*.csv
head -5 sensor_*_raw_*.csv
```

4. **Thông tin sensor:**
   - Model sensor: _______________
   - Sensor ID: _______________
   - Measurement được chọn: _______________
