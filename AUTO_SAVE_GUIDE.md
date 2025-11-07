# Hướng dẫn tính năng TỰ ĐỘNG LƯU (Auto-Save)

## Tổng quan

GUI đã được nâng cấp với tính năng **TỰ ĐỘNG LƯU** dữ liệu trong khi recording. Bạn không cần phải click "Save All CSV" nữa - dữ liệu sẽ được lưu liên tục vào file CSV!

## Cách hoạt động

### 1. Khi bắt đầu recording (Click "Start Recording")

- Một file CSV mới được tạo tự động trong thư mục `recordings_upsampled/`
- Tên file: `recording_YYYYMMDD_HHMMSS_upsampled_50Hz.csv`
- Log panel sẽ hiển thị: `Auto-save: Enabled (will save to CSV every 200ms)`

**Ví dụ:**
```
[12:11:58] Recording started (target 50.0Hz upsampled)
[12:11:58] Connected sensors: C
[12:11:58] Auto-save: Enabled (will save to CSV every 200ms)
[12:11:58] Auto CSV: C:\Users\...\recordings_upsampled\recording_20251107_121158_upsampled_50Hz.csv
```

### 2. Trong khi recording

- **Mỗi 200ms** (0.2 giây), dữ liệu upsampled mới sẽ được ghi vào CSV
- Console (terminal) sẽ hiển thị: `[AUTO-SAVE] Wrote X rows to CSV`
- Dữ liệu được **flush** ngay lập tức để đảm bảo an toàn (ngay cả khi app crash)

**Ví dụ console output:**
```
[AUTO-SAVE] Wrote 15 rows to CSV
[AUTO-SAVE] Wrote 12 rows to CSV
[AUTO-SAVE] Wrote 18 rows to CSV
...
```

### 3. Khi dừng recording (Click "Stop")

- Dữ liệu còn lại được ghi hết vào file
- File được đóng an toàn
- Log panel sẽ hiển thị: `✓ Auto-saved to: recording_20251107_121158_upsampled_50Hz.csv`

**Ví dụ:**
```
[12:12:36] Recording stopped
[12:12:36]   Sensor C: 245 raw, 1926 upsampled samples
[12:12:36] ✓ Auto-saved to: recording_20251107_121158_upsampled_50Hz.csv
```

## Format file CSV

File CSV có format như sau:

```csv
time_s,A,B,C
0.012345,9.8123,,
0.032456,9.7845,,10.2341
0.052567,9.8234,,-0.1234
...
```

- **Cột 1**: `time_s` - Timestamp (giây)
- **Cột 2**: Giá trị upsampled của Sensor A (nếu connected)
- **Cột 3**: Giá trị upsampled của Sensor B (nếu connected)
- **Cột 4**: Giá trị upsampled của Sensor C (nếu connected)

Nếu sensor không connected, cột sẽ để trống.

## Ưu điểm

### ✅ An toàn dữ liệu
- Dữ liệu được lưu liên tục, không lo mất data nếu:
  - App bị crash
  - Máy tính tắt đột ngột
  - Quên không click "Save"

### ✅ Không cần thao tác thủ công
- Không cần click "Save All CSV"
- Không cần chọn thư mục
- Không cần đặt tên file

### ✅ Ghi theo thời gian thực
- Mỗi 200ms (5 lần/giây) có batch mới được ghi
- Dữ liệu luôn được cập nhật kịp thời

### ✅ Tối ưu hiệu suất
- Chỉ ghi dữ liệu MỚI (không ghi lại dữ liệu cũ)
- Sử dụng `last_written_index` để track vị trí đã ghi

## Quy trình sử dụng

### Cách cũ (Không khuyến khích)
```
1. Connect sensor
2. Start Recording
3. Đợi 30 giây
4. Stop
5. Click "Save All CSV" ← Dễ quên!
6. Chọn thư mục
7. Đợi ghi file
```

### Cách mới (Tự động) ✨
```
1. Connect sensor
2. Start Recording
3. Đợi 30 giây
4. Stop
5. ✅ XONG! File đã sẵn trong thư mục recordings_upsampled/
```

## Kiểm tra dữ liệu

### Trong quá trình recording

Mở terminal/command prompt và chạy:
```bash
# Windows
type recordings_upsampled\recording_*.csv | more

# Linux/Mac
tail -f recordings_upsampled/recording_*.csv
```

Bạn sẽ thấy dữ liệu được cập nhật liên tục!

### Sau khi stop recording

```bash
# Kiểm tra file size
dir recordings_upsampled\*.csv         # Windows
ls -lh recordings_upsampled/*.csv      # Linux/Mac

# Đếm số dòng
find /c /v "" recordings_upsampled\recording_*.csv   # Windows
wc -l recordings_upsampled/recording_*.csv           # Linux/Mac

# Xem 10 dòng đầu
head -10 recordings_upsampled/recording_*.csv
```

## Vị trí file

File CSV tự động được lưu tại:
- **Windows**: `C:\Users\<Tên>\Desktop\pasco_python\recordings_upsampled\`
- **Linux**: `/path/to/pasco_python/recordings_upsampled/`

## Lưu ý quan trọng

### ⚠️ KHÔNG click "Start Recording" lại sau khi Stop

Nếu bạn click "Start Recording" lại, buffer sẽ bị xóa và file CSV MỚI sẽ được tạo.

**Đúng:**
```
Start → Stop → Xem file → Disconnect → Connect → Start mới
```

**Sai:**
```
Start → Stop → Start lại ← Buffer bị xóa!
```

### ⚠️ File CSV sẽ bị ghi đè nếu tên trùng

Vì tên file dựa trên timestamp (chính xác đến giây), nếu bạn Start/Stop/Start trong cùng 1 giây, file cũ sẽ bị ghi đè.

**Khuyến nghị**: Đợi ít nhất 1-2 giây giữa các lần recording.

### ⚠️ Thư mục recordings_upsampled phải tồn tại

App sẽ tự động tạo thư mục nếu chưa có, nhưng nếu bạn xóa thư mục trong khi đang recording, sẽ xảy ra lỗi.

## Troubleshooting

### Không thấy [AUTO-SAVE] trong console

**Nguyên nhân**: Console output có thể bị buffer

**Giải pháp**:
```bash
# Chạy với unbuffered output
python -u examples/gui_multi_sensor_upsampled.py
```

### File CSV rỗng sau khi stop

**Nguyên nhân**: Có thể sensor không trả về dữ liệu hoặc measurement chưa được chọn

**Giải pháp**:
1. Kiểm tra Log panel có dòng "First sample received!" không
2. Kiểm tra Stats panel có hiển thị "Raw:X Up:Y" không
3. Xem TROUBLESHOOTING_CSV.md để debug chi tiết

### File CSV không có timestamp đều

**Nguyên nhân**: Upsampling dựa trên dữ liệu thô có sẵn

**Giải pháp**: Đây là hành vi bình thường. Upsampling sẽ tạo timestamps đều hơn nhưng không hoàn hảo 100% vì:
- Bluetooth có jitter
- Sensor đôi khi miss sample
- Buffer size giới hạn

### Muốn lưu cả raw data

**Giải pháp**: Sử dụng nút "Save All CSV" sau khi stop để lưu:
- File `sensor_X_raw_*.csv` - Dữ liệu gốc từ sensor
- File `sensor_X_upsampled_*.csv` - Dữ liệu upsampled riêng cho từng sensor

Auto-save chỉ lưu **combined upsampled data** của tất cả sensors.

## So sánh với "Save All CSV"

| Tính năng | Auto-Save | Save All CSV |
|-----------|-----------|--------------|
| Thời điểm | Liên tục (mỗi 200ms) | Sau khi stop, thủ công |
| Format | 1 file merged (A,B,C) | Nhiều file riêng lẻ |
| Dữ liệu | Chỉ upsampled | Cả raw và upsampled |
| An toàn | ✅ Cao (auto-flush) | ⚠️ Phụ thuộc user |
| Thao tác | ✅ Tự động | ❌ Thủ công |

**Khuyến nghị**: Sử dụng cả hai!
- Auto-save: Đảm bảo không mất dữ liệu
- Save All CSV: Backup và phân tích chi tiết từng sensor

## Ví dụ workflow hoàn chỉnh

```bash
# 1. Chạy GUI
python examples/gui_multi_sensor_upsampled.py 2>&1 | tee session.log

# 2. Trong GUI:
#    - Connect Sensor C (ID: 964-462)
#    - Chọn measurement: "Accelerationx"
#    - Click "Start Recording"
#    - Quan sát trong 30 giây
#    - Click "Stop"

# 3. Kiểm tra file
ls -lh recordings_upsampled/recording_*.csv

# 4. Xem nội dung
head -20 recordings_upsampled/recording_*.csv

# 5. Phân tích trong Python/Excel/MATLAB
python
>>> import pandas as pd
>>> df = pd.read_csv('recordings_upsampled/recording_20251107_121158_upsampled_50Hz.csv')
>>> df.head()
>>> df.plot(x='time_s', y='C')
```

## Kết luận

Tính năng auto-save giúp:
- ✅ Không mất dữ liệu
- ✅ Tiết kiệm thời gian
- ✅ Tự động hóa workflow
- ✅ An toàn hơn khi thu thập dữ liệu dài

**Thử ngay**: Pull code mới nhất và test tính năng auto-save!

```bash
git pull origin claude/setup-venv-pasco-011CUsnqbc5s6Wp4Gd4gHdNn
venv-pasco/bin/python examples/gui_multi_sensor_upsampled.py
```
