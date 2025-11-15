# 🧪 HƯỚNG DẪN TEST VỚI DỮ LIỆU THẬT

## 📊 Dữ liệu của bạn

```
sensor_data/
  sample_0/
    amag_g: 0.99543
    ax_g: 0.00275
    ay_g: 0.00067
    az_g: 0.99542
    gx_dps: 0.0916
    gy_dps: -0.03053
    gz_dps: 0
    pitch_kf: -0.00581
    roll_kf: 0.01715
    time_ms: 9589
  sample_1/...
  sample_2/...
  ...
```

---

## 🚀 CÁCH TEST

### **Option 1: Test với dữ liệu sẵn có trong Firebase**

1. **Start Backend:**
```cmd
C:\PBL4\AIBackend\start_backend.bat
```

2. **Run Test Script:**
```cmd
C:\PBL4\AIBackend\run_test.bat
→ Chọn 2 (Test with existing data)
```

Script sẽ:
- ✅ Lấy 40 samples từ Realtime DB
- ✅ Gửi từng sample vào API
- ✅ Hiển thị kết quả prediction

---

### **Option 2: Upload test data rồi test**

1. **Upload dữ liệu mẫu:**
```cmd
C:\PBL4\AIBackend\run_test.bat
→ Chọn 1 (Upload test data)
→ Chọn activity type (STANDING/WALKING)
```

2. **Test prediction:**
```cmd
C:\PBL4\AIBackend\run_test.bat
→ Chọn 2 (Test with existing data)
```

---

### **Option 3: Tự động (Upload + Test)**

```cmd
C:\PBL4\AIBackend\run_test.bat
→ Chọn 3 (Both)
```

---

## 📈 KẾT QUẢ MẪU

### Test realtime (gửi từng sample):
```
[1/40] Buffering... (need 39 more)
[2/40] Buffering... (need 38 more)
...
[40/40] Buffering... (need 0 more)

🎯 PREDICTION RESULT:
   Activity: STANDING
   Confidence: 95.23%
   Probabilities:
     WALKING:    2.15%
     UPSTAIRS:   0.53%
     DOWNSTAIRS: 0.82%
     SITTING:    0.34%
     STANDING:   95.23% ████████████████████████████████████
     RUNNING:    0.93%
```

### Test manual (gửi 40 samples cùng lúc):
```
🎯 PREDICTION RESULT:
   Activity: STANDING
   Confidence: 95.23%

   Probabilities:
     WALKING      [ 2.15%] █
     UPSTAIRS     [ 0.53%] 
     DOWNSTAIRS   [ 0.82%] 
     SITTING      [ 0.34%] 
     STANDING     [95.23%] ███████████████████████████████████████████████
     RUNNING      [ 0.93%] 
```

---

## 🔍 PHÂN TÍCH DỮ LIỆU CỦA BẠN

Dựa vào dữ liệu `sample_0`:
```
ax_g: 0.00275  (gần 0)
ay_g: 0.00067  (gần 0)
az_g: 0.99542  (~ 1g - hướng xuống)
gx_dps: 0.0916 (gần 0)
gy_dps: -0.03053 (gần 0)
gz_dps: 0 (không quay)
```

→ **Đặc điểm:** Gia tốc chỉ theo trục Z (~1g), không có chuyển động
→ **Dự đoán:** Có thể là **STANDING** hoặc **SITTING**

---

## 📝 CÁC API ENDPOINTS ĐỂ TEST

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Send Single Sample
```bash
curl -X POST http://localhost:8000/sensor_data \
  -H "Content-Type: application/json" \
  -d '{
    "ax_g": 0.00275,
    "ay_g": 0.00067,
    "az_g": 0.99542,
    "gx_dps": 0.0916,
    "gy_dps": -0.03053,
    "gz_dps": 0,
    "amag_g": 0.99543,
    "pitch_kf": -0.00581,
    "roll_kf": 0.01715,
    "timestamp": 9589
  }'
```

### 3. Manual Prediction (40 samples)
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @samples.json
```

### 4. Get Recent Predictions
```bash
curl http://localhost:8000/predictions/recent?limit=10
```

### 5. Get Statistics
```bash
curl http://localhost:8000/statistics/user1?days=7
```

---

## ⚙️ TROUBLESHOOTING

### Backend không chạy?
```bash
cd C:\PBL4\AIBackend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Không kết nối Firebase?
- Kiểm tra `serviceAccountKey.json`
- Kiểm tra `databaseURL` trong code

### Model không load?
- Kiểm tra file `AI/models/best_model.h5`
- Kiểm tra TensorFlow version

### Dữ liệu không có trong Realtime DB?
```bash
# Upload test data
python upload_test_data.py
```

---

## 🎯 NEXT STEPS

1. **Upload dữ liệu thật từ ESP32** lên Firebase
2. **Run backend** để listen & predict
3. **View results** trong Firestore
4. **Display in Flutter** app

---

**Chạy test ngay:**
```cmd
C:\PBL4\AIBackend\run_test.bat
```

🎉 Good luck!
