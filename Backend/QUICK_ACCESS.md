# Quick Access Links

## 🚀 Khởi động Server

Chạy file: `start_server.bat`

hoặc trong terminal:
```bash
cd Backend
python main.py
```

## 🌐 Truy cập API

Sau khi server đã chạy, mở trình duyệt và truy cập:

### API Root
- **http://localhost:8000** ✅
- **http://127.0.0.1:8000** ✅

### API Documentation (Swagger UI)
- **http://localhost:8000/docs** 📚

### Alternative API Docs (ReDoc)
- **http://localhost:8000/redoc** 📖

### Health Check
- **http://localhost:8000/health** ❤️

## ⚠️ LƯU Ý QUAN TRỌNG

**KHÔNG** truy cập `http://0.0.0.0:8000` ❌

- `0.0.0.0` là địa chỉ đặc biệt chỉ dùng cho server config
- Trình duyệt KHÔNG thể truy cập địa chỉ này
- Thay vào đó, sử dụng `localhost` hoặc `127.0.0.1`

## 📝 API Endpoints

### General
- `GET /` - Root endpoint
- `GET /health` - Health check

### Prediction
- `POST /predict/single` - Single sensor prediction
- `POST /predict/batch` - Batch prediction

### Firebase
- `POST /firebase/start` - Start Firebase listener
- `POST /firebase/stop` - Stop Firebase listener

### Buffer
- `GET /buffer/status` - Buffer status
- `POST /buffer/clear` - Clear buffer

## 🧪 Test API

Sử dụng Swagger UI tại `http://localhost:8000/docs` để test các endpoints interactively.

hoặc dùng curl:

```bash
# Health check
curl http://localhost:8000/health

# Test prediction
curl -X POST "http://localhost:8000/predict/single" -H "Content-Type: application/json" -d "{\"ax_g\":0.05,\"ay_g\":0.98,\"az_g\":0.15,\"gx_dps\":1.2,\"gy_dps\":-0.5,\"gz_dps\":0.3,\"amag_g\":1.01,\"pitch_kf\":5.2,\"roll_kf\":2.8}"
```

## 🔧 Troubleshooting

### Server không khởi động được
- Kiểm tra đã activate virtual environment chưa
- Kiểm tra đã cài đặt dependencies: `pip install -r requirements.txt`
- Kiểm tra model file tồn tại: `../AI/final_model_test_PHONG_QUANG.h5`

### Web không lên
- ✅ Sử dụng `localhost:8000` không phải `0.0.0.0:8000`
- Kiểm tra firewall có block port 8000 không
- Kiểm tra server đã chạy thành công chưa (xem terminal output)

### Port đã được sử dụng
- Đổi port trong `main.py` (dòng 408)
- hoặc kill process đang dùng port 8000
