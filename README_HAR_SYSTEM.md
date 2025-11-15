# 🎯 PBL4 - Human Activity Recognition System

## 📋 Tổng quan hệ thống

### Kiến trúc:
```
ESP32 (Bluetooth) → COM5 → Firebase Realtime DB
                                    ↓
                            FastAPI Backend
                            (AI Model H5)
                                    ↓
                            Firestore Database
                                    ↓
                            Flutter App
                            (Statistics & UI)
```

---

## 🔧 Components

### 1. **ESP32**
- Đọc dữ liệu IMU (gia tốc kế + con quay hồi chuyển)
- Gửi qua Bluetooth Serial (COM5 - Incoming)
- Format: `ax,ay,az,gx,gy,gz,amag,pitch,roll`

### 2. **Firebase Realtime Database**
- Nhận dữ liệu sensor từ ESP32
- Node: `/sensor_data`
- Realtime streaming

### 3. **FastAPI Backend** (`C:\PBL4\AIBackend\`)
- Listen Firebase Realtime DB
- Buffer 40 samples (sliding window)
- Preprocessing:
  - Tính derivatives (d_pitch, d_roll)
  - QuantileTransformer
  - StandardScaler
- AI Model (H5) prediction
- Lưu kết quả vào Firestore

### 4. **Firestore Database**
- Collection: `activity_predictions`
- Fields:
  - `user_id`
  - `activity` (WALKING, RUNNING, etc.)
  - `confidence`
  - `probabilities`
  - `timestamp`

### 5. **Flutter App** (`C:\PBL4\PBL4_Backend\flutter_app\`)
- Giao diện người dùng
- Xem statistics từ Firestore
- Charts & visualizations
- Realtime updates

---

## 🚀 Cài đặt & Chạy

### Bước 1: Setup Firebase
1. Tạo Firebase project tại [console.firebase.google.com](https://console.firebase.google.com)
2. Enable Realtime Database
3. Enable Firestore
4. Download `serviceAccountKey.json` và đặt vào `C:\PBL4\AIBackend\`

### Bước 2: Upload ESP32 Code
```cpp
#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("PBL4_HAR");
  // Init IMU...
}

void loop() {
  // Read IMU data
  float ax, ay, az, gx, gy, gz, amag, pitch, roll;
  
  // Send via Bluetooth
  SerialBT.print(ax); SerialBT.print(",");
  SerialBT.print(ay); SerialBT.print(",");
  // ... etc
  SerialBT.println(roll);
  
  delay(50); // 20Hz
}
```

### Bước 3: Pair Bluetooth
```cmd
C:\PBL4\auto_pair_bluetooth.bat
```
- Chọn "PBL4_HAR"
- Ghi nhớ COM5 (Incoming)

### Bước 4: Start FastAPI Backend
```cmd
C:\PBL4\AIBackend\start_backend.bat
```
- Backend sẽ chạy tại: http://localhost:8000
- API docs: http://localhost:8000/docs

### Bước 5: Run Flutter App
```cmd
cd C:\PBL4\PBL4_Backend\flutter_app
flutter pub get
flutter run -d chrome
```

---

## 📊 Luồng dữ liệu chi tiết

### 1. ESP32 → Firebase Realtime DB
```
ESP32 gửi qua Bluetooth → COM5
     ↓
Python script hoặc Node.js
     ↓
Firebase Realtime DB: /sensor_data
```

### 2. FastAPI Listen & Process
```python
# main.py
def listen_to_realtime_db():
    sensor_ref = realtime_db.child('sensor_data')
    sensor_ref.listen(on_data_change)
    
def on_data_change(event):
    # Add to buffer
    data_buffer.add_data(event.data)
    
    # Get 40 samples window
    if len(buffer) >= 40:
        # Preprocess
        X = preprocess_window(buffer)
        
        # Predict
        prediction = model.predict(X)
        
        # Save to Firestore
        save_prediction_to_firestore(prediction)
```

### 3. Preprocessing
```python
# Input: 40 samples x 9 features (raw)
# → Add derivatives (d_pitch, d_roll)
# → 40 x 11 features
# → QuantileTransformer (fit on train data)
# → StandardScaler
# → Output: (1, 40, 11) for model
```

### 4. AI Model Prediction
```
Model Input: (1, 40, 11)
Model: LSTM/GRU/Transformer
Output: 6 classes probabilities
Predicted activity: argmax(probabilities)
```

### 5. Save to Firestore
```javascript
firestore_db.collection('activity_predictions').add({
  user_id: 'user1',
  activity: 'WALKING',
  confidence: 0.95,
  probabilities: {...},
  timestamp: SERVER_TIMESTAMP
})
```

### 6. Flutter Display
```dart
// Get statistics
final stats = await HARApiService()
  .getUserStatistics(userId: 'user1', days: 7);

// Display in UI
- Pie chart
- Activity list
- Real-time updates (every 5s)
```

---

## 🔗 API Endpoints

### GET `/health`
Check backend status
```json
{
  "status": "healthy",
  "model": "loaded",
  "buffer_size": 35,
  "last_prediction": {...}
}
```

### POST `/sensor_data`
Gửi sensor data (alternative to Realtime DB)
```json
{
  "ax_g": 0.5,
  "ay_g": 0.2,
  "az_g": 9.8,
  "gx_dps": 0.1,
  "gy_dps": 0.2,
  "gz_dps": 0.3,
  "amag_g": 9.8,
  "pitch_kf": 10.5,
  "roll_kf": 5.2,
  "timestamp": 1234567890
}
```

### GET `/predictions/recent?limit=10`
Get recent predictions

### GET `/statistics/{user_id}?days=7`
Get user activity statistics

### DELETE `/buffer/clear`
Clear data buffer

---

## 📱 Flutter Screens

### 1. **Home Screen**
- Overview
- Quick actions
- Current activity

### 2. **Activity Statistics Screen**
- Time range selector (1, 7, 14, 30 days)
- Summary cards (total activities)
- Pie chart (activity distribution)
- Activity list with percentages

### 3. **Console Screen**
- View raw sensor data
- Debug mode

---

## 🧪 Testing

### Test Backend
```bash
# Health check
curl http://localhost:8000/health

# Manual prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

### Test Flutter
```dart
// Call API
final result = await HARApiService()
  .getUserStatistics(userId: 'user1');
print(result);
```

---

## 📦 Project Structure

```
C:\PBL4\
├── AIBackend/
│   ├── main.py              # FastAPI server
│   ├── requirements.txt
│   ├── start_backend.bat
│   ├── serviceAccountKey.json
│   └── AI/
│       ├── models/
│       │   └── best_model.h5
│       └── src/
│           └── preprocessing.py
│
├── PBL4_Backend/
│   └── flutter_app/
│       ├── lib/
│       │   ├── main.dart
│       │   ├── services/
│       │   │   ├── har_api_service.dart
│       │   │   └── web_serial_service.dart
│       │   └── screens/
│       │       ├── activity_statistics_screen.dart
│       │       └── bluetooth_console_screen_fixed.dart
│       └── pubspec.yaml
│
├── auto_pair_bluetooth.bat
├── check_bluetooth.bat
├── quick_start_monitor.bat
└── run_all.bat
```

---

## ✅ Checklist

- [ ] Firebase project created
- [ ] serviceAccountKey.json downloaded
- [ ] ESP32 code uploaded
- [ ] Bluetooth paired (COM5)
- [ ] Backend running
- [ ] Flutter app running
- [ ] Seeing predictions in Firestore
- [ ] Statistics displayed in app

---

## 🎉 Quick Start

```cmd
# 1. Pair Bluetooth
C:\PBL4\auto_pair_bluetooth.bat

# 2. Start Backend
C:\PBL4\AIBackend\start_backend.bat

# 3. Run Flutter
C:\PBL4\PBL4_Backend\flutter_app> flutter run -d chrome

# Done! View statistics in app 🎊
```

---

## 🐛 Troubleshooting

### Backend không kết nối Firestore?
- Kiểm tra `serviceAccountKey.json`
- Kiểm tra Firebase Database URL

### Model không load?
- Kiểm tra file `best_model.h5` có tồn tại
- Kiểm tra TensorFlow version

### Flutter không gọi được API?
- Kiểm tra backend đang chạy
- Kiểm tra URL: http://localhost:8000

---

**Made with ❤️ for PBL4 Project**
