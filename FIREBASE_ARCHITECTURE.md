# Cấu trúc dữ liệu Firebase cho hệ thống Human Activity Recognition

## 1. Firebase Realtime Database (ESP32 → Flutter)

### Cấu trúc JSON từ ESP32:
```json
{
  "imu_data": {
    "time_ms": 1704067200000,    // Unix timestamp (milliseconds)
    "ax_g": 0.98,                // Acceleration X (g)
    "ay_g": -0.02,               // Acceleration Y (g)
    "az_g": 0.15,                // Acceleration Z (g)
    "gx_dps": 1.23,              // Gyroscope X (degrees per second)
    "gy_dps": -0.45,             // Gyroscope Y (degrees per second)
    "gz_dps": 0.67,              // Gyroscope Z (degrees per second)
    "amag_g": 1.02,              // Acceleration magnitude (g)
    "pitch_kf": -3.1,            // Pitch angle from Kalman filter (degrees)
    "roll_kf": 5.2               // Roll angle from Kalman filter (degrees)
  }
}
```

### Code ESP32 (Arduino):
```cpp
#include <WiFi.h>
#include <FirebaseESP32.h>
#include <Wire.h>
#include <MPU6050.h>

FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;

MPU6050 mpu;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  mpu.initialize();
  
  WiFi.begin("YOUR_SSID", "YOUR_PASSWORD");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
  }
  
  config.database_url = "https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app/";
  config.api_key = "AIzaSyCancHOOZLpBlGTZo9SZI8HNS22B71Fu1E";
  
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
}

void loop() {
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  
  // Convert to proper units
  float accelX = ax / 16384.0;  // ±2g range
  float accelY = ay / 16384.0;
  float accelZ = az / 16384.0;
  float gyroX = gx / 131.0;     // ±250°/s range
  float gyroY = gy / 131.0;
  float gyroZ = gz / 131.0;
  
  // Calculate acceleration magnitude
  float amag = sqrt(accelX * accelX + accelY * accelY + accelZ * accelZ);
  
  // Calculate roll and pitch (simple calculation, use Kalman filter for better results)
  float roll_kf = atan2(accelY, accelZ) * 180.0 / PI;
  float pitch_kf = atan2(-accelX, sqrt(accelY * accelY + accelZ * accelZ)) * 180.0 / PI;
  
  // Create JSON with new field names
  FirebaseJson json;
  json.set("time_ms", millis());
  json.set("ax_g", accelX);
  json.set("ay_g", accelY);
  json.set("az_g", accelZ);
  json.set("gx_dps", gyroX);
  json.set("gy_dps", gyroY);
  json.set("gz_dps", gyroZ);
  json.set("amag_g", amag);
  json.set("pitch_kf", pitch_kf);
  json.set("roll_kf", roll_kf);
  
  // Send to Firebase
  Firebase.setJSON(firebaseData, "/imu_data", json);
  
  delay(50);  // 20Hz sampling rate
}
```

## 2. Firestore Collections (Flutter → Firestore)

### Collection: `activities`
```json
{
  "userId": "user123",
  "activity": "Chạy",
  "startTime": Timestamp(2024-01-01 10:30:00),
  "endTime": Timestamp(2024-01-01 10:35:00),
  "duration": 300,              // seconds
  "confidence": 0.95,           // 0.0 - 1.0
  "caloriesBurned": 45.5,
  "createdAt": Timestamp(2024-01-01 10:35:00)
}
```

### Collection: `notifications`
```json
{
  "userId": "user123",
  "type": "sitting_warning",
  "title": "Cảnh báo ngồi quá lâu",
  "message": "Bạn đã ngồi liên tục 30 phút. Hãy đứng dậy hoạt động!",
  "isRead": false,
  "createdAt": Timestamp(2024-01-01 11:00:00)
}
```

### Collection: `users`
```json
{
  "username": "Nguyễn Văn A",
  "email": "user@example.com",
  "weight": 70.0,               // kg
  "createdAt": Timestamp(2024-01-01 09:00:00)
}
```

## 3. Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only read/write their own data
    match /activities/{activityId} {
      allow read, write: if request.auth != null && 
                           request.auth.uid == resource.data.userId;
    }
    
    match /notifications/{notificationId} {
      allow read, write: if request.auth != null && 
                           request.auth.uid == resource.data.userId;
    }
    
    match /users/{userId} {
      allow read, write: if request.auth != null && 
                           request.auth.uid == userId;
    }
  }
}
```

## 4. Realtime Database Rules

```json
{
  "rules": {
    "imu_data": {
      ".read": true,
      ".write": true
    }
  }
}
```

## 5. Flutter Stream Listener

Trong `imu_service.dart`:
```dart
void startListening() {
  _imuRef.onValue.listen((event) {
    if (event.snapshot.value != null) {
      final data = event.snapshot.value as Map;
      _processImuData(data);
    }
  });
}
```

## 6. Luồng xử lý hoàn chỉnh

```
ESP32 (50ms) → Firebase Realtime DB (/imu_data)
                      ↓
              Flutter ImuService.startListening()
                      ↓
              Thu thập 40 samples (2 giây)
                      ↓
              TFLite model.run() → predict activity
                      ↓
              Activity thay đổi?
                      ↓
              FirestoreService.saveActivity()
                      ↓
              Firestore (/activities/{id})
                      ↓
              UI Screens (StreamBuilder) → Real-time update
```

## 7. Tính năng tự động thông báo

```dart
// Trong imu_service.dart
void _checkSittingDuration() {
  if (_currentActivity == 'Ngồi') {
    final duration = DateTime.now().difference(_activityStartTime!);
    if (duration.inMinutes >= 30) {
      FirestoreService.createSittingWarning(duration.inMinutes);
    }
  }
}
```
