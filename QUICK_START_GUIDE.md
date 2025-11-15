# 🚀 QUICK START - PBL4 HAR SYSTEM

## ⚡ Chạy nhanh trong 5 phút!

### **Bước 1: Setup Backend** (chỉ làm 1 lần)

```cmd
C:\PBL4\AIBackend\setup_backend.bat
```

✅ Tạo virtual environment
✅ Cài đặt tất cả packages
✅ Sẵn sàng chạy

---

### **Bước 2: Test hệ thống**

```cmd
C:\PBL4\test_full_system.bat
```

Script sẽ tự động:
1. ✅ Upload 40 samples test data lên Firebase
2. ✅ Start backend server
3. ✅ Predict với AI model
4. ✅ Lưu kết quả vào Firestore
5. ✅ (Optional) Chạy Flutter app

---

### **Bước 3: Xem kết quả**

#### **Trong Terminal (Backend logs):**
```
🎯 Prediction: WALKING (95.2%)
✅ Saved to Firestore
```

#### **Trong Firebase Console:**
```
https://console.firebase.google.com/
→ Firestore Database
→ activity_predictions collection
→ Thấy document mới
```

#### **Trong Flutter App:**
```
Home Screen → Card "Hoạt động hiện tại"
→ 🚶 Đang đi bộ (95.2%)
```

---

## 📱 Chạy Flutter App riêng

```cmd
cd C:\PBL4\PBL4_Backend\flutter_app
flutter run -d chrome
```

**Thay đổi main.dart để dùng realtime screen:**

```dart
// lib/main.dart
import 'screens/home_screen_realtime.dart';

home: const HomeScreen(), // Sẽ tự động stream activity
```

---

## 🔥 Luồng hoạt động realtime:

```
Backend predict mới
        ↓
Save to Firestore
        ↓
.snapshots() trigger
        ↓
StreamBuilder rebuild
        ↓
UI update với animation
```

**Tốc độ:** < 500ms từ prediction → hiển thị!

---

## 🧪 Test các activities khác nhau:

### **Test STANDING:**
```cmd
cd C:\PBL4\AIBackend
python upload_test_data.py
→ Chọn 1 (STANDING)
```

### **Test WALKING:**
```cmd
python upload_test_data.py
→ Chọn 2 (WALKING)
```

Sau đó run:
```cmd
python test_realtime_db.py
→ Chọn 2 (manual prediction)
```

---

## 🎨 Kết quả mong đợi:

### **WALKING:**
```
┌─────────────────────────┐
│        🚶             │
│                         │
│  Hoạt động hiện tại    │
│  🚶 Đang đi bộ         │
│  95.2%                 │
└─────────────────────────┘
Color: Blue
```

### **STANDING:**
```
┌─────────────────────────┐
│        🧍             │
│                         │
│  Hoạt động hiện tại    │
│  🧍 Đang đứng          │
│  92.8%                 │
└─────────────────────────┘
Color: Teal
```

---

## ⚠️ Troubleshooting

### Backend không chạy?
```cmd
cd C:\PBL4\AIBackend
venv\Scripts\activate
pip list  # Check installed packages
python -c "import fastapi; import tensorflow; print('OK')"
```

### Flutter không hiển thị activity?
1. Check Firestore có data không
2. Check console logs (F12)
3. Verify `activity_service.dart` đã import

### Model không predict?
- Check file `AI/models/best_model.h5` tồn tại
- Check logs: "Model loaded successfully"

---

## 📂 Files quan trọng:

| File | Mục đích |
|------|----------|
| `test_full_system.bat` | Test toàn bộ hệ thống |
| `home_screen_realtime.dart` | UI với realtime stream |
| `activity_service.dart` | Service listen Firestore |
| `main.py` | Backend server với AI |

---

## 🎯 Next Steps:

1. ✅ **Test với dữ liệu thật từ ESP32**
   - Upload code ESP32
   - Connect Bluetooth
   - Gửi data realtime

2. ✅ **Deploy backend**
   - Host trên cloud (Railway, Render, etc.)
   - Update Firebase rules

3. ✅ **Build Flutter app**
   - `flutter build web`
   - `flutter build apk`

---

## 📞 Support:

Nếu gặp lỗi, check:
1. Backend logs
2. Flutter console (F12)
3. Firebase console

---

**Chạy ngay:**
```cmd
C:\PBL4\test_full_system.bat
```

🎉 **Enjoy your HAR system!**
