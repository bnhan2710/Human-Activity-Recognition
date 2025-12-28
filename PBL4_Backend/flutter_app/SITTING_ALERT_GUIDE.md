# Hệ thống Cảnh báo Ngồi Quá Lâu Real-time

## Tổng quan

Hệ thống tự động theo dõi hoạt động của người dùng và gửi thông báo real-time khi phát hiện ngồi quá 5 phút liên tục.

## Kiến trúc

```
ESP32 → Firebase Realtime DB → Backend AI → Firestore
                                                ↓
                                    activity_predictions
                                                ↓
                            ActivityMonitorService (Flutter)
                                                ↓
                                    Real-time Alert + Notification
```

## Thành phần

### 1. ActivityMonitorService (`activity_monitor_service.dart`)

**Chức năng:**
- Lắng nghe Firestore collection `activity_predictions` real-time
- Theo dõi hoạt động SITTING liên tục
- Tích lũy thời gian ngồi
- Trigger cảnh báo khi vượt ngưỡng 5 phút (300 giây)
- Lưu thông báo vào Firestore collection `notifications`

**Cơ chế hoạt động:**

```dart
// 1. Subscribe to latest prediction
FirebaseFirestore.instance
    .collection('activity_predictions')
    .where('user_id', isEqualTo: 'user1')
    .orderBy('created_at', descending: true)
    .limit(1)
    .snapshots()
    .listen((snapshot) { ... });

// 2. Track sitting duration
if (activity == 'SITTING') {
    _totalSittingSeconds += duration_seconds;
    
    if (_totalSittingSeconds >= 300) {
        _triggerSittingAlert();
    }
} else {
    _resetSitting();
}

// 3. Save notification to Firestore
await FirebaseFirestore.instance.collection('notifications').add({
    'user_id': 'user1',
    'title': 'Cảnh báo: Ngồi quá lâu!',
    'message': 'Bạn đã ngồi hơn 5 phút...',
    'type': 'sitting_alert',
    'duration_minutes': 5,
    'is_read': false,
    'created_at': FieldValue.serverTimestamp(),
});
```

**API:**
- `startMonitoring()` - Bắt đầu theo dõi
- `stopMonitoring()` - Dừng theo dõi
- `getSittingStatus()` - Lấy trạng thái ngồi hiện tại
- `onSittingAlert` - Callback khi có cảnh báo
- `onActivityChange` - Callback khi hoạt động thay đổi

### 2. Home Screen Integration

**Tích hợp:**
```dart
final ActivityMonitorService _monitorService = ActivityMonitorService();

@override
void initState() {
    super.initState();
    _startActivityMonitoring();
}

void _startActivityMonitoring() {
    // Set callbacks
    _monitorService.onSittingAlert = (message, duration) {
        _showSittingAlert(message);
    };
    
    // Start monitoring
    _monitorService.startMonitoring();
}
```

**UI Response:**
- **Dialog**: Hiển thị cảnh báo đầy đủ với gợi ý sức khỏe
- **SnackBar**: Thông báo nhẹ với nút "Xem" để mở màn hình thông báo
- **Navigation**: Có thể chuyển đến NotificationsScreen

### 3. Notifications Screen (`notifications_screen_firebase.dart`)

**Cập nhật:**
- Hiển thị thông báo từ collection `notifications`
- Phân biệt loại thông báo qua field `type`
- `sitting_alert` có icon 🪑 và màu cam
- Hiển thị thời gian ngồi (`duration_minutes`)
- Đánh dấu đã đọc khi click

**Query:**
```dart
FirebaseFirestore.instance
    .collection('notifications')
    .where('user_id', isEqualTo: 'user1')
    .orderBy('created_at', descending: true)
    .snapshots();
```

## Firestore Schema

### Collection: `notifications`

```json
{
  "user_id": "user1",
  "title": "Cảnh báo: Ngồi quá lâu!",
  "message": "Bạn đã ngồi hơn 5 phút. Hãy đứng dậy và vận động...",
  "type": "sitting_alert",
  "duration_minutes": 5,
  "is_read": false,
  "created_at": Timestamp,
  "timestamp": "2024-11-15T10:35:20.000Z"
}
```

**Fields:**
- `user_id`: ID người dùng (string)
- `title`: Tiêu đề thông báo (string)
- `message`: Nội dung chi tiết (string)
- `type`: Loại thông báo - `sitting_alert`, `info`, etc. (string)
- `duration_minutes`: Thời gian ngồi (int)
- `is_read`: Đã đọc chưa (boolean)
- `created_at`: Server timestamp (Timestamp)
- `timestamp`: ISO 8601 string (string)

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

### 3. Chạy Flutter App

```bash
cd c:\PBL4\PBL4_Backend\flutter_app
flutter run -d chrome
```

### 4. Test Sitting Alert

**Tự nhiên:**
1. ESP32 gửi sensor data
2. Backend predict SITTING liên tục
3. Sau 5 phút (300s tích lũy), alert được trigger

**Manual test (development):**
```dart
// Trong development, có thể test bằng cách:
// 1. Tạo nhiều predictions SITTING trong Firestore
// 2. Hoặc thay đổi threshold từ 300s → 30s để test nhanh

// ActivityMonitorService.dart, line ~72
if (_totalSittingSeconds >= 30) { // Test với 30s thay vì 300s
    _triggerSittingAlert();
}
```

## Luồng hoạt động

### Real-time Flow

```
1. ESP32 sends sensor data (every 50ms)
   ↓
2. Backend AI predicts activity (every 2s)
   ↓
3. Prediction saved to Firestore with:
   - activity: "SITTING"
   - duration_seconds: 2.0
   - start_time, end_time
   ↓
4. ActivityMonitorService detects new prediction
   ↓
5. If SITTING:
   - Accumulate: _totalSittingSeconds += 2.0
   - Check: if >= 300s → Alert
   ↓
6. Alert triggered:
   - Save to Firestore notifications
   - Call onSittingAlert callback
   ↓
7. Home Screen shows:
   - AlertDialog with health tips
   - SnackBar with "Xem" button
   ↓
8. User can view in NotificationsScreen
```

### Reset Logic

```
When activity changes from SITTING to anything else:
1. Reset _sittingStartTime = null
2. Reset _totalSittingSeconds = 0
3. Reset _hasNotifiedFiveMinutes = false
4. Log total sitting duration
```

## Tính năng

### ✅ Đã hoàn thành

- [x] Real-time monitoring từ Firestore
- [x] Tích lũy thời gian ngồi chính xác
- [x] Trigger alert sau 5 phút
- [x] Lưu notification vào Firestore
- [x] Hiển thị dialog cảnh báo
- [x] Hiển thị snackbar
- [x] Màn hình thông báo với phân loại
- [x] Đánh dấu đã đọc
- [x] Icon và màu sắc theo loại thông báo
- [x] Auto-reset khi đổi hoạt động

### 🚀 Có thể mở rộng

- [ ] Cấu hình threshold (5, 10, 15 phút)
- [ ] Thông báo nhắc nhở định kỳ (mỗi giờ)
- [ ] Thống kê thời gian ngồi trong ngày
- [ ] Cảnh báo nhiều cấp độ (warning, danger)
- [ ] Push notification (FCM)
- [ ] Vibration/Sound alert
- [ ] Tích hợp với Health Kit
- [ ] Gamification (điểm thưởng khi vận động)

## Troubleshooting

### Alert không xuất hiện

1. **Kiểm tra monitoring có chạy không:**
   ```dart
   print('Monitoring active: ${_monitorService != null}');
   ```

2. **Kiểm tra predictions có đến không:**
   ```dart
   // Trong ActivityMonitorService._handleNewPrediction()
   print('📊 Activity: $activity, Duration: $durationSeconds');
   ```

3. **Kiểm tra tích lũy thời gian:**
   ```dart
   print('🪑 Total sitting: $_totalSittingSeconds seconds');
   ```

4. **Kiểm tra threshold:**
   ```dart
   if (_totalSittingSeconds >= 300) { // Đảm bảo đúng 300s
   ```

### Thông báo không lưu vào Firestore

1. **Kiểm tra Firestore rules:**
   ```javascript
   match /notifications/{notificationId} {
     allow read, write: if true; // Hoặc custom rules
   }
   ```

2. **Xem Firebase Console:**
   - Mở Firestore console
   - Kiểm tra collection `notifications`
   - Verify documents được tạo

3. **Check logs:**
   ```dart
   print('✅ Notification saved to Firestore'); // Success
   print('❌ Error saving notification: $e'); // Error
   ```

### Dialog không hiển thị

1. **Kiểm tra mounted:**
   ```dart
   if (!mounted) return; // Phải check trước showDialog
   ```

2. **Kiểm tra callback:**
   ```dart
   _monitorService.onSittingAlert = (message, duration) {
       print('Alert callback triggered!');
       _showSittingAlert(message);
   };
   ```

## Performance

### Resource Usage

- **Memory**: ~5-10MB cho ActivityMonitorService
- **CPU**: Minimal (event-driven, không polling)
- **Network**: Real-time snapshots (WebSocket connection)
- **Battery**: Low impact (chỉ lắng nghe 1 document)

### Optimization

- Sử dụng `.limit(1)` để giảm data transfer
- Stream chỉ theo dõi document mới nhất
- Auto-cleanup khi dispose
- Không lưu duplicate notifications

## Security

### Firestore Rules (recommended)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Activity predictions - read only
    match /activity_predictions/{predictionId} {
      allow read: if request.auth != null;
      allow write: if false; // Only backend can write
    }
    
    // Notifications - user-specific
    match /notifications/{notificationId} {
      allow read: if request.auth != null && 
                    resource.data.user_id == request.auth.uid;
      allow create: if request.auth != null;
      allow update: if request.auth != null && 
                      resource.data.user_id == request.auth.uid;
      allow delete: if false; // Soft delete only
    }
  }
}
```

## Kết luận

Hệ thống cảnh báo ngồi quá lâu đã hoàn chỉnh với:
- ✅ Real-time monitoring
- ✅ Accurate time tracking
- ✅ User-friendly alerts
- ✅ Persistent notifications
- ✅ Health tips integration

**Next steps:** Test với real ESP32 data và thu thập feedback từ người dùng!
