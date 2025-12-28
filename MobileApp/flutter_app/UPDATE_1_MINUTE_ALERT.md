# ✅ Cập Nhật: Thông Báo Ngồi Quá 1 Phút

## 🔔 Thay đổi

### Trước (cũ):
- Cảnh báo khi ngồi **> 5 phút (300 giây)**
- Lưu notification với message "ngồi hơn 5 phút"

### Sau (mới):
- Cảnh báo khi ngồi **> 1 phút (60 giây)** ✨
- Lưu notification với message "ngồi hơn 1 phút"

## 📝 File đã sửa

### 1. `activity_monitor_service.dart`

**Thay đổi:**
```dart
// CŨ:
bool _hasNotifiedFiveMinutes = false;
if (_totalSittingSeconds >= 300 && !_hasNotifiedFiveMinutes) {
  _triggerSittingAlert();
}

// MỚI:
bool _hasNotifiedOneMinute = false;
if (_totalSittingSeconds >= 60 && !_hasNotifiedOneMinute) {
  _triggerSittingAlert();
}
```

**Message notification:**
```dart
// CŨ:
'Bạn đã ngồi hơn 5 phút...'

// MỚI:
'Bạn đã ngồi hơn 1 phút. Hãy đứng dậy và vận động...'
```

## 🎯 Luồng hoạt động

```
1. ESP32 gửi sensor data → Backend AI
   ↓
2. Backend predict: SITTING
   ↓
3. Lưu vào Firestore activity_predictions
   ↓
4. ActivityMonitorService lắng nghe real-time
   ↓
5. Tích lũy thời gian ngồi: 2s → 4s → 6s → ... → 60s
   ↓
6. Khi đạt 60 giây (1 phút):
   - Gọi _triggerSittingAlert()
   - Lưu notification vào Firestore
   - Hiển thị AlertDialog
   - Hiển thị SnackBar
   ↓
7. User xem thông báo trong NotificationsScreenFirebase
```

## 📊 Firestore Notification Structure

```json
{
  "user_id": "user1",
  "title": "Cảnh báo: Ngồi quá lâu!",
  "message": "Bạn đã ngồi hơn 1 phút. Hãy đứng dậy và vận động để tốt cho sức khỏe.",
  "type": "sitting_alert",
  "duration_minutes": 1,
  "is_read": false,
  "created_at": Timestamp,
  "timestamp": "2024-11-15T10:35:20.000Z"
}
```

## 🎨 Màn hình Thông Báo

### NotificationsScreenFirebase
**Hiển thị:**
- ✅ Nhóm tất cả thông báo
- ✅ Sort theo thời gian mới nhất
- ✅ Icon màu cam cho sitting_alert
- ✅ Highlight chưa đọc (background màu cam nhạt)
- ✅ Hiển thị "X giờ trước", "Y phút trước"
- ✅ Click để đánh dấu đã đọc

**Layout:**
```
┌─────────────────────────────────┐
│ Thông báo sức khỏe       [←]   │
├─────────────────────────────────┤
│                                 │
│ 🟠 Cảnh báo: Ngồi quá lâu! •   │
│    Bạn đã ngồi hơn 1 phút...   │
│    5 phút trước                 │
├─────────────────────────────────┤
│ 🟠 Cảnh báo: Ngồi quá lâu!     │
│    Bạn đã ngồi hơn 1 phút...   │
│    1 giờ trước                  │
├─────────────────────────────────┤
│ 🟠 Cảnh báo: Ngồi quá lâu!     │
│    Bạn đã ngồi hơn 1 phút...   │
│    1 ngày trước                 │
└─────────────────────────────────┘
```

## 🚀 Test

### Bước 1: Hot Restart
```
Press R in Flutter terminal
```

### Bước 2: Chờ 1 phút
- Ngồi yên không cử động
- Backend sẽ predict SITTING liên tục
- Sau 60 giây → Alert xuất hiện!

### Bước 3: Xem thông báo
- AlertDialog xuất hiện ngay lập tức
- SnackBar có nút "Xem"
- Click "Xem" → Mở NotificationsScreenFirebase
- Thấy notification mới nhất ở đầu danh sách

## ⚙️ Cấu hình tùy chỉnh

### Thay đổi threshold:

**1 phút:**
```dart
if (_totalSittingSeconds >= 60 && !_hasNotifiedOneMinute) {
```

**30 giây (test nhanh):**
```dart
if (_totalSittingSeconds >= 30 && !_hasNotifiedOneMinute) {
```

**2 phút:**
```dart
if (_totalSittingSeconds >= 120 && !_hasNotifiedOneMinute) {
```

## 📈 Thống kê theo ngày

Notifications hiện tại:
- ✅ Lưu với `created_at` timestamp
- ✅ Sort theo thời gian giảm dần
- ✅ Hiển thị "X ngày trước"

Nếu muốn **nhóm theo ngày**:
```dart
// Group notifications by date
Map<String, List<DocumentSnapshot>> groupedByDate = {};

for (var doc in notifications) {
  var data = doc.data() as Map<String, dynamic>;
  var createdAt = (data['created_at'] as Timestamp?)?.toDate();
  
  if (createdAt != null) {
    String dateKey = DateFormat('yyyy-MM-dd').format(createdAt);
    groupedByDate[dateKey] = groupedByDate[dateKey] ?? [];
    groupedByDate[dateKey]!.add(doc);
  }
}

// Display with headers
for (var entry in groupedByDate.entries) {
  String displayDate = _getDisplayDate(entry.key);
  // Show header: "Hôm nay", "Hôm qua", "15/11/2024"
  // Show notifications for that day
}
```

## ✨ Features

### Đã có:
- [x] Cảnh báo sau 1 phút ngồi
- [x] Lưu notification vào Firestore
- [x] Hiển thị trong NotificationsScreenFirebase
- [x] AlertDialog + SnackBar
- [x] Icon màu cam cho sitting alert
- [x] Highlight chưa đọc
- [x] Đánh dấu đã đọc khi click
- [x] Hiển thị thời gian "X giờ trước"

### Có thể mở rộng:
- [ ] Nhóm thông báo theo ngày (Hôm nay, Hôm qua, ...)
- [ ] Thống kê số lần ngồi quá lâu/ngày
- [ ] Biểu đồ xu hướng ngồi
- [ ] Xóa thông báo cũ
- [ ] Filter theo loại (sitting_alert, info, ...)
- [ ] Push notification (FCM)
- [ ] Âm thanh cảnh báo

## 🎯 Kết quả

**Trước:**
- Chờ 5 phút mới có cảnh báo
- Quá lâu, người dùng đã ngồi quá nhiều

**Sau:**
- Chỉ 1 phút là có cảnh báo ✅
- Nhắc nhở kịp thời
- Tốt hơn cho sức khỏe
- User experience tốt hơn

**Perfect cho health monitoring! 🏃‍♂️💪**
