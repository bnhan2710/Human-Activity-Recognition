# 🎯 LUỒNG HOẠT ĐỘNG HOÀN CHỈNH

## 📊 Tóm tắt:

```
ESP32 (IMU) → Realtime DB → FastAPI → AI Model → Firestore → Flutter App
```

---

## 🔄 Chi tiết từng bước:

### **1. ESP32 gửi dữ liệu**
```
ESP32 đọc IMU (MPU6050)
  → ax, ay, az (gia tốc)
  → gx, gy, gz (con quay hồi chuyển)
  → pitch, roll (góc nghiêng)
  
→ Gửi qua Bluetooth/WiFi
→ Firebase Realtime Database: /sensor_data
```

### **2. FastAPI Backend listen & process**
```python
# main.py
listen_to_realtime_db():
  ↓
Buffer 40 samples (2 seconds @ 20Hz)
  ↓
Preprocess:
  - Tính derivatives (d_pitch, d_roll)
  - QuantileTransformer
  - StandardScaler
  - Shape: (1, 40, 11)
  ↓
AI Model predict
  ↓
Result: {
  activity: "WALKING",
  confidence: 0.95,
  probabilities: {...}
}
  ↓
Save to Firestore: /activity_predictions
```

### **3. Firestore lưu kết quả**
```
Collection: activity_predictions
Document: {
  user_id: "user1",
  activity: "WALKING",
  confidence: 0.95,
  probabilities: {
    WALKING: 0.95,
    RUNNING: 0.02,
    ...
  },
  timestamp: SERVER_TIMESTAMP
}
```

### **4. Flutter App hiển thị realtime**
```dart
// activity_service.dart
Stream<Map> listenCurrentActivity() {
  return firestore
    .collection('activity_predictions')
    .where('user_id', '==', 'user1')
    .orderBy('timestamp', descending: true)
    .limit(1)
    .snapshots();
}

// home_screen.dart
StreamBuilder(
  stream: activityStream,
  builder: (context, snapshot) {
    final activity = snapshot.data['activity'];
    final confidence = snapshot.data['confidence'];
    
    return ActivityCard(
      icon: getIcon(activity),    // 🚶 / 🏃 / 🪑
      color: getColor(activity),  // Blue / Red / Purple
      text: getDisplayName(activity),
      confidence: confidence
    );
  }
)
```

---

## 🎨 Hiển thị trên Flutter

### **Card "Hoạt động hiện tại":**

```
┌─────────────────────────────┐
│         🚶 (Icon)          │
│                             │
│   Hoạt động hiện tại       │
│   🚶 Đang đi bộ            │
│   95.2% confidence         │
└─────────────────────────────┘
```

**Khi activity thay đổi:**
- Icon thay đổi: 🚶 → 🏃 → 🪑
- Màu thay đổi: Blue → Red → Purple
- Text thay đổi: "Đang đi bộ" → "Đang chạy" → "Đang ngồi"
- Animation: Scale + Fade transition
- **Realtime** - Không cần refresh!

---

## 🔥 Các activities & biểu tượng:

| Activity | Icon | Color | Display Text |
|----------|------|-------|--------------|
| WALKING | 🚶 `directions_walk` | Blue | Đang đi bộ |
| RUNNING | 🏃 `directions_run` | Red | Đang chạy |
| UPSTAIRS | ⬆️ `arrow_upward` | Green | Đang lên cầu thang |
| DOWNSTAIRS | ⬇️ `arrow_downward` | Orange | Đang xuống cầu thang |
| SITTING | 🪑 `chair` | Purple | Đang ngồi |
| STANDING | 🧍 `accessibility_new` | Teal | Đang đứng |

---

## 📱 Code Flutter chính:

### **1. ActivityService** (`activity_service.dart`)
```dart
Stream<Map<String, dynamic>> listenCurrentActivity({String userId = 'user1'}) {
  return firestore
      .collection('activity_predictions')
      .where('user_id', isEqualTo: userId)
      .orderBy('timestamp', descending: true)
      .limit(1)
      .snapshots()
      .map((snapshot) => snapshot.docs.first.data());
}
```

### **2. HomeScreen** (`home_screen.dart`)
```dart
StreamBuilder<Map<String, dynamic>>(
  stream: _activityService.listenCurrentActivity(),
  builder: (context, snapshot) {
    if (snapshot.hasData) {
      final activity = snapshot.data!['activity'];
      final confidence = snapshot.data!['confidence'];
      
      return ActivityCard(
        icon: _getActivityIcon(activity),
        color: _getActivityColor(activity),
        title: 'Hoạt động hiện tại',
        subtitle: _getActivityDisplayName(activity),
        confidence: confidence,
      );
    }
    return LoadingCard();
  }
)
```

---

## ⚡ Realtime Updates

**Cách hoạt động:**
1. Backend predict → Save to Firestore
2. Firestore triggers `.snapshots()` stream
3. StreamBuilder rebuild với data mới
4. UI update với animation

**Tần suất update:**
- Backend predict: ~2s (40 samples @ 20Hz)
- Firestore update: Realtime
- Flutter rebuild: Instant (< 100ms)

---

## 🧪 Test luồng hoàn chỉnh:

### **Bước 1: Start Backend**
```cmd
C:\PBL4\AIBackend\start_backend.bat
```

### **Bước 2: Upload test data**
```cmd
cd C:\PBL4\AIBackend
python upload_test_data.py
→ Chọn WALKING hoặc STANDING
```

### **Bước 3: Test prediction**
```cmd
python test_realtime_db.py
→ Chọn option 2 (manual prediction)
```

Kết quả sẽ lưu vào Firestore.

### **Bước 4: Run Flutter App**
```cmd
cd C:\PBL4\PBL4_Backend\flutter_app
flutter run -d chrome
```

→ Xem card "Hoạt động hiện tại" update realtime!

---

## 📊 Firestore Structure:

```
activity_predictions/
  {document_id}/
    user_id: "user1"
    activity: "WALKING"
    confidence: 0.95
    probabilities: {
      WALKING: 0.95,
      RUNNING: 0.02,
      UPSTAIRS: 0.01,
      DOWNSTAIRS: 0.01,
      SITTING: 0.005,
      STANDING: 0.005
    }
    timestamp: Timestamp
    created_at: "2025-01-14T00:10:23.456Z"
```

---

## ✅ Files quan trọng:

| File | Mô tả |
|------|-------|
| `AIBackend/main.py` | FastAPI backend với AI model |
| `flutter_app/lib/services/activity_service.dart` | Service listen Firestore |
| `flutter_app/lib/screens/home_screen.dart` | UI hiển thị activity |
| `AIBackend/test_realtime_db.py` | Script test |
| `AIBackend/upload_test_data.py` | Upload sample data |

---

🎉 **Hoàn tất! Activity sẽ update realtime trên Flutter app!**
