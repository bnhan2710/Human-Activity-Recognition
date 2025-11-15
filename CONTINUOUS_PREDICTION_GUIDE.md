# 🔄 CONTINUOUS PREDICTION SYSTEM

## ✨ Tính năng mới:

### **1. Background Listener**
- Liên tục listen Realtime Database
- Tự động detect data mới
- Predict ngay khi có đủ samples

### **2. Smart Buffer**
- Lưu 40 samples gần nhất
- Nếu không có data mới → Dùng lại 40 samples cũ
- Không bị gián đoạn prediction

### **3. Activity Session Tracking**
- Theo dõi khi activity thay đổi
- Lưu session (activity + duration) vào Firestore
- Collection: `activity_sessions`

### **4. Auto Save**
- Mỗi prediction → Firestore `activity_predictions`
- Mỗi activity kết thúc → Firestore `activity_sessions`

---

## 🗄️ Firestore Structure:

### **Collection: `activity_predictions`** (Current)
```json
{
  "user_id": "user1",
  "activity": "WALKING",
  "confidence": 0.952,
  "probabilities": {...},
  "timestamp": Timestamp
}
```

### **Collection: `activity_sessions`** (New)
```json
{
  "user_id": "user1",
  "activity": "WALKING",
  "duration": 45.2,  // seconds
  "start_time": Timestamp,
  "end_time": Timestamp,
  "timestamp": Timestamp
}
```

---

## 🔄 Luồng hoạt động:

```
ESP32 gửi data liên tục
        ↓
Realtime DB: sensor_data/{timestamp}/sample_X
        ↓
Backend listener detect new timestamp
        ↓
Add samples to buffer (keep last 40)
        ↓
Có đủ 40 samples? 
  → Yes: Predict với samples mới
  → No: Dùng lại 40 samples cũ
        ↓
Prediction result
        ↓
Activity thay đổi?
  → Yes: Save previous session to Firestore
  → No: Continue
        ↓
Save current prediction to Firestore
        ↓
Flutter StreamBuilder nhận update
        ↓
UI thay đổi với animation
```

---

## ⚡ Tốc độ xử lý:

- **Listener delay:** < 500ms (Firebase realtime)
- **Prediction:** ~1-2s (40 samples processing)
- **Firestore write:** < 100ms
- **Flutter update:** < 50ms
- **Total:** < 3 giây từ sensor → UI

---

## 📊 Ví dụ Session:

### **Scenario:**
```
00:00 - User STANDING (30s)
00:30 - User starts WALKING (60s)
01:30 - User starts RUNNING (45s)
02:15 - User stops SITTING
```

### **Firestore `activity_sessions`:**
```
Doc 1: {activity: "STANDING", duration: 30}
Doc 2: {activity: "WALKING", duration: 60}
Doc 3: {activity: "RUNNING", duration: 45}
```

### **Firestore `activity_predictions`:**
```
Liên tục update (mỗi 2-3s):
- STANDING (92%)
- STANDING (93%)
- WALKING (95%)  ← Activity changed, saved session
- WALKING (96%)
- RUNNING (89%)  ← Activity changed, saved session
...
```

---

## 🧪 Test:

### **Bước 1: Start Backend với Listener**
```cmd
cd C:\PBL4\AIBackend
uvicorn main:app --reload
```

Output:
```
🚀 Starting HAR System...
============================================================
✅ Background listener started
✅ System ready!
   API: http://localhost:8000
   Docs: http://localhost:8000/docs
============================================================

👂 Starting Firebase Realtime Database listener...
   Listening for new sensor data...
✅ Realtime DB listener started!
   Waiting for new data...
```

### **Bước 2: Simulate Data Stream**
```cmd
# Upload WALKING data
python upload_test_data.py
→ Chọn 2 (WALKING)
```

Backend output:
```
📥 New data: Timestamp 167890 with 10 samples
🤖 Predicting with 40 samples...
✅ Predicted: WALKING (95.2%)
✅ Saved to Firestore
```

### **Bước 3: Change Activity**
```cmd
# Upload RUNNING data
python upload_test_data.py
→ Generate RUNNING samples (modify script)
```

Backend output:
```
📥 New data: Timestamp 170123 with 10 samples
🤖 Predicting with 40 samples...
✅ Saved activity session: WALKING (45.2s)  ← Previous activity
✅ Predicted: RUNNING (89.3%)  ← New activity
✅ Saved to Firestore
```

### **Bước 4: Flutter Auto Update**
```
Home Screen Card:
🚶 Đang đi bộ (Blue) 95.2%
        ↓ (animation)
🏃 Đang chạy (Red) 89.3%
```

---

## 🔍 Check Results:

### **Firebase Console:**

#### **activity_predictions** (realtime updates)
```
Latest doc:
  activity: "RUNNING"
  confidence: 0.893
  timestamp: 2025-01-14 10:23:45
```

#### **activity_sessions** (completed activities)
```
Doc 1:
  activity: "WALKING"
  duration: 45.2
  start_time: 2025-01-14 10:22:00
  end_time: 2025-01-14 10:22:45

Doc 2:
  activity: "RUNNING"
  duration: 30.5
  start_time: 2025-01-14 10:22:45
  end_time: 2025-01-14 10:23:15
```

---

## 🎯 Key Features:

✅ **Continuous prediction** - Không cần trigger manual
✅ **Smart buffering** - Reuse last 40 if no new data
✅ **Session tracking** - Save activity duration
✅ **Realtime UI** - Flutter auto update
✅ **No interruption** - Always have 40 samples ready

---

## 📝 Next Steps:

1. ✅ Backend với continuous listener
2. ✅ Session tracking
3. ✅ Flutter realtime UI
4. 🔜 Add analytics screen
5. 🔜 Add activity history chart

**Chạy backend và xem magic happen!** 🚀✨
