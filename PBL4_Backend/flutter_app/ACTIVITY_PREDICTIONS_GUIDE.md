# Hướng dẫn sử dụng Thống kê Calo và Lịch sử Hoạt động

## Tổng quan

Hệ thống đã được cập nhật để lưu thêm thông tin thời gian vào Firestore collection `activity_predictions`:

### Dữ liệu được lưu trong Firestore

Mỗi prediction hiện có các trường sau:

```json
{
  "activity": "WALKING",
  "confidence": 0.95,
  "probabilities": {
    "WALKING": 0.95,
    "RUNNING": 0.03,
    "SITTING": 0.01,
    ...
  },
  "user_id": "user1",
  "created_at": "2024-11-15T10:30:45.123456",
  "timestamp": FirestoreTimestamp,
  "start_time": "2024-11-15T10:30:43.000000",    // MỚI
  "end_time": "2024-11-15T10:30:45.000000",      // MỚI
  "duration_seconds": 2.0                         // MỚI
}
```

### Các trường mới

1. **start_time**: Thời điểm bắt đầu hoạt động (ISO 8601 format)
   - Lấy từ timestamp của sample đầu tiên trong window (40 samples)
   
2. **end_time**: Thời điểm kết thúc hoạt động (ISO 8601 format)
   - Lấy từ timestamp của sample cuối cùng trong window
   
3. **duration_seconds**: Thời lượng hoạt động (giây)
   - Tính bằng: `(end_time - start_time)` / 1000
   - Mặc định: 2.0 giây (window size 40 samples @ 20Hz)

## Backend Changes

### File: `firebase_handler.py`

```python
def save_prediction_to_firestore(
    self, 
    activity: str, 
    confidence: float, 
    probabilities: Dict[str, float],
    user_id: str = "user1",
    collection: str = "activity_predictions",
    start_time: Optional[datetime] = None,      # NEW
    end_time: Optional[datetime] = None,        # NEW
    duration_seconds: Optional[float] = None    # NEW
) -> str:
```

### File: `main.py`

Trong hàm `handle_firebase_data()`, thêm logic tính toán thời gian:

```python
# Tính thời gian từ buffer
buffer_data = list(data_buffer.buffer)
window_samples = buffer_data[-data_buffer.window_size:]

if window_samples and 'timestamp' in window_samples[0]:
    start_timestamp_ms = window_samples[0]['timestamp']
    start_time = datetime.fromtimestamp(start_timestamp_ms / 1000.0)
    
    end_timestamp_ms = window_samples[-1]['timestamp']
    end_time = datetime.fromtimestamp(end_timestamp_ms / 1000.0)
    
    duration_seconds = (end_timestamp_ms - start_timestamp_ms) / 1000.0
else:
    # Fallback nếu không có timestamp
    end_time = datetime.now()
    duration_seconds = 2.0
    start_time = end_time - timedelta(seconds=duration_seconds)

# Lưu với thời gian
doc_id = firebase_handler.save_prediction_to_firestore(
    activity=activity,
    confidence=float(confidence),
    probabilities=probabilities,
    user_id=user_id,
    collection=collection,
    start_time=start_time,          # Thêm
    end_time=end_time,              # Thêm
    duration_seconds=duration_seconds  # Thêm
)
```

## Flutter Screens

### 1. Màn hình Thống kê Calo (`calo_screen_predictions.dart`)

**Tính năng:**
- Hiển thị tổng Calo tiêu hao trong ngày
- Tổng thời gian hoạt động
- Số lượng hoạt động
- Phân tích chi tiết theo từng loại hoạt động
- Biểu đồ cột: Calo theo hoạt động
- Biểu đồ cột: Thời lượng theo hoạt động

**Cách tính Calo:**
```dart
final Map<String, double> caloriesPerMinute = {
  'WALKING': 3.5,     // Calo/phút
  'RUNNING': 9.0,
  'UPSTAIRS': 7.0,
  'DOWNSTAIRS': 5.0,
  'SITTING': 1.0,
  'STANDING': 1.5,
};

// Calo = (duration_seconds / 60) * caloriesPerMinute[activity]
```

**Query Firestore:**
```dart
FirebaseFirestore.instance
    .collection('activity_predictions')
    .where('user_id', isEqualTo: 'user1')
    .where('start_time', isGreaterThanOrEqualTo: startOfDay.toIso8601String())
    .where('start_time', isLessThan: endOfDay.toIso8601String())
    .orderBy('start_time', descending: false)
    .snapshots()
```

### 2. Màn hình Lịch sử Hoạt động (`history_screen_predictions.dart`)

**Tính năng:**
- Danh sách các hoạt động theo thứ tự thời gian (mới nhất trước)
- Hiển thị: Tên hoạt động, thời gian bắt đầu - kết thúc, thời lượng, độ tin cậy
- Click vào hoạt động để xem chi tiết:
  - Thời gian bắt đầu/kết thúc chính xác
  - Thời lượng
  - Độ tin cậy
  - Xác suất các hoạt động khác (với progress bar)

**Query Firestore:**
```dart
FirebaseFirestore.instance
    .collection('activity_predictions')
    .where('user_id', isEqualTo: 'user1')
    .where('start_time', isGreaterThanOrEqualTo: startOfDay.toIso8601String())
    .where('start_time', isLessThan: endOfDay.toIso8601String())
    .orderBy('start_time', descending: true)  // Mới nhất trước
    .snapshots()
```

### 3. Cập nhật Home Screen

Màn hình chính đã được cập nhật để điều hướng đến các màn hình mới:
- Nút "Thống kê Calo" → `CaloScreenPredictions`
- Nút "Lịch sử hoạt động" → `HistoryScreenPredictions`

## Cách sử dụng

### 1. Khởi động Backend

```bash
cd c:\PBL4\AIBackend\backend
python main.py
```

### 2. Bắt đầu Firebase Stream

```bash
python start_stream.py
```

hoặc qua API:

```bash
curl -X POST http://127.0.0.1:8000/firebase/start
```

### 3. Chạy Flutter App

```bash
cd c:\PBL4\PBL4_Backend\flutter_app
flutter run -d chrome
```

### 4. Sử dụng App

1. **Màn hình chính**: Xem hoạt động hiện tại real-time
2. **Thống kê Calo**: 
   - Chọn ngày muốn xem
   - Xem tổng Calo tiêu hao
   - Xem chi tiết từng hoạt động
   - Xem biểu đồ phân tích
3. **Lịch sử Hoạt động**:
   - Chọn ngày muốn xem
   - Xem danh sách hoạt động
   - Click vào hoạt động để xem chi tiết

## Firestore Index yêu cầu

Để query hoạt động tốt, cần tạo các composite index trong Firestore:

### Index 1: Calo Screen Query
```
Collection: activity_predictions
Fields:
  - user_id (Ascending)
  - start_time (Ascending)
  - __name__ (Ascending)
```

### Index 2: History Screen Query
```
Collection: activity_predictions
Fields:
  - user_id (Ascending)
  - start_time (Descending)
  - __name__ (Descending)
```

**Cách tạo:**
1. Chạy Flutter app và mở màn hình Calo/History
2. Firebase sẽ báo lỗi và đưa link tạo index
3. Click vào link và chờ index được tạo (3-5 phút)

## Lưu ý

### Backend
- ✅ KHÔNG thay đổi logic AI/Model
- ✅ KHÔNG thay đổi logic kết nối Firebase
- ✅ CHỈ thêm tính toán thời gian và lưu thêm 3 trường

### Flutter
- Sử dụng `user_id = 'user1'` mặc định (giống backend)
- Hỗ trợ chọn ngày để xem lịch sử
- Real-time updates qua Firestore snapshots
- Cần package `fl_chart` cho biểu đồ

### Dữ liệu mẫu

Để test, backend sẽ tự động lưu predictions khi nhận được sensor data từ ESP32:
- Mỗi 2 giây (40 samples @ 20Hz) sẽ có 1 prediction
- Mỗi prediction có đầy đủ thông tin thời gian
- Dữ liệu được lưu tự động vào Firestore

## Troubleshooting

### Backend không lưu thời gian
- Kiểm tra log terminal: Phải thấy dòng `⏰ Thời gian: HH:MM:SS → HH:MM:SS (X.XXs)`
- Kiểm tra samples có trường `timestamp`

### Flutter không hiển thị dữ liệu
1. Kiểm tra Firestore console: Có data trong `activity_predictions` không?
2. Kiểm tra `user_id = 'user1'` khớp với backend
3. Kiểm tra các index đã được tạo chưa
4. Chọn đúng ngày có dữ liệu

### Calo không chính xác
- Calo tính theo công thức ước lượng: `duration_minutes * calories_per_minute`
- Có thể điều chỉnh trong `caloriesPerMinute` map

## Kết luận

Hệ thống hiện đã hoàn chỉnh:
1. ✅ Backend lưu đầy đủ thông tin thời gian
2. ✅ Flutter hiển thị Thống kê Calo với biểu đồ
3. ✅ Flutter hiển thị Lịch sử Hoạt động chi tiết
4. ✅ Real-time updates từ Firestore
5. ✅ UI đẹp, dễ sử dụng

Tất cả đều đọc từ collection `activity_predictions` do backend AI tạo ra!
