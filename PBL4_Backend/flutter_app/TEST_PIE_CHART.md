# Test Pie Chart - History Screen

## Quick Test Steps

### 1. Đảm bảo có dữ liệu
```bash
# Backend phải đang chạy
cd c:\PBL4\AIBackend\backend
python main.py

# ESP32 phải đang push data
# Hoặc chạy script upload test data
```

### 2. Hot Restart Flutter
```
Press R in terminal
```

### 3. Vào màn hình Lịch sử
```
Home Screen → Bottom Nav → History (📜 icon)
```

### 4. Kiểm tra biểu đồ
Bạn sẽ thấy:
- ✅ Biểu đồ tròn ở trên cùng
- ✅ "Thống kê hoạt động trong ngày"
- ✅ "Tổng thời gian: Xh Yp"
- ✅ Màu sắc cho từng hoạt động
- ✅ Legend bên phải với:
  - Tên hoạt động (tiếng Việt)
  - Thời gian (Xp Ys)
  - Phần trăm (XX.X%)

### 5. Test với ngày khác
```
Click "Chọn ngày" → Chọn ngày có dữ liệu
```

## Expected Output

### Ví dụ với dữ liệu thật:
```
╔══════════════════════════════════════╗
║ Thống kê hoạt động trong ngày        ║
║ Tổng thời gian: 2h 15p               ║
║                                      ║
║  ┌──────────┐    🟣 Ngồi            ║
║  │    58%   │    1h 18p (58.2%)     ║
║  │  ┌───┐   │                       ║
║  │  │10%│   │    🟢 Đi bộ           ║
║  │  └───┘   │    38p (28.1%)        ║
║  │    28%   │                       ║
║  └──────────┘    🔴 Chạy            ║
║                  13p 30s (10.0%)    ║
║                                      ║
║                  🔵 Lên cầu thang   ║
║                  4p 30s (3.3%)      ║
╚══════════════════════════════════════╝
```

## Visual Check

### Colors:
- 🟣 Purple → SITTING (Ngồi)
- 🟢 Green → WALKING (Đi bộ)
- 🔴 Red → RUNNING (Chạy)
- 🔵 Blue → UPSTAIRS (Lên cầu thang)
- 🟠 Orange → DOWNSTAIRS (Xuống cầu thang)
- 🔷 Teal → STANDING (Đứng)

### Numbers:
- Phần trăm trên chart = Phần trăm trong legend ✅
- Tổng % ≈ 100% (có thể 99.9% - 100.1% do làm tròn)
- Tổng thời gian = Sum của các hoạt động ✅

## Troubleshooting

### Không thấy biểu đồ
1. Check console logs:
   ```javascript
   🔍 Query Firestore: user_id=user1
   📊 Total docs: X
   📅 Filtering for date: ...
   ```

2. Check Firestore:
   - Firebase Console → Firestore
   - Collection: activity_predictions
   - Filter: user_id = 'user1'
   - Check created_at dates

3. Đảm bảo có index:
   - user_id + timestamp (descending)

### Biểu đồ có nhưng trống
- Chọn ngày khác (hôm nay hoặc hôm qua)
- Check backend đang chạy
- Check ESP32 đang push data

### Màu sắc lạ
- Check activity names trong Firestore
- Should be: WALKING, RUNNING, SITTING, etc.
- Not: walking, run, sit, etc.

### Legend bị cắt
- Normal nếu có nhiều activities
- Có thể scroll trong legend
- Hoặc expand screen size

## Performance Test

### Metrics to check:
- Initial load: < 500ms
- Switch date: < 200ms
- Chart animation: smooth
- No lag when scrolling list

### Browser DevTools:
```
F12 → Performance tab
Record → Switch date → Stop
Check frame rate: Should be 60fps
```

## Demo Data

Nếu không có dữ liệu thật, tạo dummy data:

```python
# c:\PBL4\AIBackend\upload_test_data.py
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

cred = credentials.Certificate('backend/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Tạo dữ liệu cho hôm nay
base_time = datetime.now().replace(hour=8, minute=0, second=0)

activities = [
    ('SITTING', 1800),   # 30 phút
    ('WALKING', 900),    # 15 phút
    ('SITTING', 3600),   # 1 giờ
    ('RUNNING', 600),    # 10 phút
    ('WALKING', 1200),   # 20 phút
    ('UPSTAIRS', 180),   # 3 phút
    ('SITTING', 2400),   # 40 phút
]

for activity, duration in activities:
    start_time = base_time
    end_time = start_time + timedelta(seconds=duration)
    
    db.collection('activity_predictions').add({
        'user_id': 'user1',
        'activity': activity,
        'confidence': 0.95,
        'probabilities': {activity: 0.95},
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': float(duration),
        'created_at': start_time.isoformat(),
        'timestamp': firestore.SERVER_TIMESTAMP,
    })
    
    base_time = end_time

print('✅ Test data created!')
```

Run:
```bash
cd c:\PBL4\AIBackend
python upload_test_data.py
```

## Success Criteria

- [x] Biểu đồ hiển thị đúng
- [x] Màu sắc phân biệt rõ
- [x] Phần trăm chính xác
- [x] Thời gian format đẹp
- [x] Legend đầy đủ thông tin
- [x] Tổng thời gian đúng
- [x] Responsive trên mobile/desktop
- [x] Không có lỗi console
- [x] Performance tốt

## Screenshots Checklist

Chụp màn hình để verify:
1. [ ] Full screen với biểu đồ
2. [ ] Zoom vào biểu đồ tròn
3. [ ] Legend với chi tiết
4. [ ] Scroll down vào list
5. [ ] Khác ngày (empty state)
6. [ ] Khác ngày (có data)

## Next Steps After Test

1. ✅ Verify biểu đồ hoạt động
2. ✅ Test với nhiều ngày khác nhau
3. ✅ Test với nhiều loại activities
4. ✅ Check performance với nhiều data
5. ✅ Test responsive trên mobile
6. 🚀 Deploy và dùng thật!

---

**Happy Testing! 📊🎉**
