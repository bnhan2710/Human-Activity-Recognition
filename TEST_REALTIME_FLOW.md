# 🎯 TEST LUỒNG HOÀN CHỈNH

## ✅ Đã cập nhật:

### **1. Backend (`main.py`)**
- `/predict` endpoint tự động lưu vào Firestore
- Mỗi prediction → Firestore document mới

### **2. Flutter (`home_screen_realtime.dart`)**
- StreamBuilder listen Firestore realtime
- AnimatedSwitcher: Tự động fade/scale khi activity thay đổi
- Icon + màu + text cập nhật tức thì

---

## 🔄 Luồng hoạt động:

```
1. Chạy backend:
   cd C:\PBL4\AIBackend
   uvicorn main:app --reload

2. Test prediction:
   python test_realtime_db.py
   → Chọn option 2
   
3. Backend predict:
   WALKING (95.2%) → Firestore
   
4. Firestore trigger:
   .snapshots() → Flutter StreamBuilder
   
5. Flutter update UI:
   Icon: 🚶 (blue)
   Text: "Đang đi bộ"
   Animation: Scale + Fade
   Confidence: 95.2%
```

---

## 🎨 Khi activity thay đổi:

### **STANDING → WALKING:**
```
Card cũ (🧍 Teal):
  Fade out (500ms)
  
Card mới (🚶 Blue):
  Fade in + Scale animation
  Icon pulse effect
```

### **WALKING → RUNNING:**
```
🚶 (Blue) → 🏃 (Red)
Animation: Elastic bounce
Duration: 600ms
```

---

## 📊 Test thay đổi activity:

### **Bước 1: Upload STANDING data**
```cmd
cd C:\PBL4\AIBackend
python upload_test_data.py
→ Chọn 1 (STANDING)
```

### **Bước 2: Test prediction**
```cmd
python test_realtime_db.py
→ Chọn 2
```

**Kết quả Flutter:**
```
Card hiển thị:
🧍 Đang đứng (Teal)
92.5% confidence
```

### **Bước 3: Upload WALKING data**
```cmd
python upload_test_data.py
→ Chọn 2 (WALKING)
```

### **Bước 4: Test lại**
```cmd
python test_realtime_db.py
→ Chọn 2
```

**Kết quả Flutter:**
```
Card tự động chuyển sang:
🚶 Đang đi bộ (Blue)
95.2% confidence

Animation: Fade out → Fade in + Scale
```

---

## 🎬 Animations:

### **1. AnimatedSwitcher**
- Duration: 500ms
- Transition: Scale + Fade
- Trigger: Khi `activity` key thay đổi

### **2. Icon Pulse**
- Duration: 600ms
- Curve: Elastic out
- Scale: 0.8 → 1.0

### **3. Color Transition**
- Gradient background
- Shadow color changes
- Smooth transition

---

## ⚡ Realtime Updates:

**Tần suất:**
- Backend predict: ~2-3 giây (40 samples @ 20Hz)
- Firestore write: < 100ms
- Flutter rebuild: < 50ms
- **Total latency: < 3.2 giây**

---

## 🧪 Test Commands:

### **Start Everything:**
```cmd
# Terminal 1: Backend
cd C:\PBL4\AIBackend
uvicorn main:app --reload

# Terminal 2: Test
python test_realtime_db.py

# Terminal 3: Flutter
cd C:\PBL4\PBL4_Backend\flutter_app
flutter run -d chrome
```

### **Watch Changes:**
1. Mở Flutter app (Home screen)
2. Chạy test prediction với data khác nhau
3. Xem card tự động thay đổi!

---

## 🎯 Kết quả mong đợi:

✅ Backend predict → Lưu Firestore
✅ Flutter listen Firestore realtime
✅ Card tự động update khi có activity mới
✅ Smooth animation (fade + scale)
✅ Icon + màu + text thay đổi
✅ Confidence % hiển thị

**Thời gian phản hồi: < 3 giây từ sensor → UI!** 🚀
