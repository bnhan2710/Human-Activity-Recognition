import numpy as np
from collections import deque
from tensorflow.keras.models import load_model
from .. import config

class IMUService:
    """
    Service xử lý dữ liệu IMU từ ESP32, lưu buffer riêng cho mỗi user_id,
    và dự đoán hành động khi đủ window_size.
    """

    def __init__(self, model_path=config.MODEL_PATH, window_size=config.WINDOW_SIZE):
        self.window_size = window_size
        self.buffers = {}  # dict user_id -> deque(samples)
        self.model = load_model(model_path)

    def add_sample(self, user_id: str, sample: list):
        """
        Thêm 1 mẫu IMU vào buffer của user_id.
        Nếu chưa có buffer, tạo mới.
        """
        if user_id not in self.buffers:
            # tạo deque mới với maxlen = window_size
            self.buffers[user_id] = deque(maxlen=self.window_size)

        # thêm mẫu mới
        self.buffers[user_id].append(sample)

        # nếu buffer đủ window_size, trả về mảng NumPy để dự đoán
        if len(self.buffers[user_id]) == self.window_size:
            return np.array(self.buffers[user_id])
        return None

    def predict_action(self, window_data: np.ndarray):
        """
        window_data: np.array shape (window_size, num_features)
        Trả về nhãn hành động dự đoán (int)
        """
        # Thêm batch dimension: (1, window_size, num_features)
        input_data = np.expand_dims(window_data, axis=0)
        pred_probs = self.model.predict(input_data)
        # chọn nhãn có xác suất cao nhất
        action_label = np.argmax(pred_probs, axis=1)[0]
        return int(action_label)

    def reset_buffer(self, user_id: str):
        """
        Xóa buffer của user_id (nếu cần, ví dụ khi logout)
        """
        if user_id in self.buffers:
            self.buffers.pop(user_id, None)
