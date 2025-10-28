from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
from ..services.imu_service import IMUService
from .. import config
from ..auth import get_current_user  # giả sử có hàm lấy user_id từ JWT token

router = APIRouter()
imu_service = IMUService()

# Lưu các kết nối WebSocket Flutter theo user_id
active_flutter_connections: Dict[str, WebSocket] = {}

# Lưu buffer IMU theo user_id
# (IMUService đã lưu buffer theo user_id nên đây là để tham khảo)
# imu_service.buffers

# =========================================
# WebSocket ESP32 gửi dữ liệu IMU
# =========================================
@router.websocket("/ws/imu")
async def imu_ws_endpoint(websocket: WebSocket):
    """
    ESP32 gửi dữ liệu IMU liên tục.
    Không cần user_id vì backend sẽ gửi nhãn dự đoán tới tất cả Flutter đang kết nối.
    """
    await websocket.accept()
    print("ESP32 connected")

    try:
        while True:
            data = await websocket.receive_json()  # dữ liệu JSON từ ESP32
            imu_sample = data.get("imu")  # {"imu": [ax, ay, az, gx, gy, gz,...]}

            # Thêm mẫu cho tất cả user_id đang có kết nối Flutter
            for user_id in active_flutter_connections.keys():
                window_data = imu_service.add_sample(user_id, imu_sample)
                if window_data is not None:
                    action_label = imu_service.predict_action(window_data)
                    # gửi nhãn dự đoán cho Flutter
                    try:
                        await active_flutter_connections[user_id].send_json({"action": action_label})
                    except:
                        # nếu gửi thất bại, bỏ connection
                        active_flutter_connections.pop(user_id, None)

    except WebSocketDisconnect:
        print("ESP32 disconnected")


# =========================================
# WebSocket Flutter nhận dự đoán
# =========================================
@router.websocket("/ws/action")
async def flutter_ws_endpoint(websocket: WebSocket, user=Depends(get_current_user)):
    """
    Flutter mở WebSocket để nhận nhãn hành động.
    user.id sẽ dùng làm user_id.
    """
    user_id = str(user.id)
    await websocket.accept()
    active_flutter_connections[user_id] = websocket
    print(f"Flutter user {user_id} connected.")

    try:
        while True:
            # Flutter không cần gửi gì, chỉ giữ kết nối mở
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"Flutter user {user_id} disconnected.")
        active_flutter_connections.pop(user_id, None)
