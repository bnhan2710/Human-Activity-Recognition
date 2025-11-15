# Placeholder for TensorFlow Lite model

This file is a placeholder. Replace it with your actual trained model.

## Model Requirements

- **Input shape**: `[1, 40, 9]`
  - 1 batch
  - 40 time steps (2 seconds at 20Hz)
  - 9 features: ax_g, ay_g, az_g, gx_dps, gy_dps, gz_dps, amag_g, pitch_kf, roll_kf

- **Output shape**: `[1, 5]`
  - 1 batch
  - 5 classes: Đứng (0), Ngồi (1), Chạy (2), Đi bộ (3), Leo cầu thang (4)

## How to train and convert model

1. Train model using TensorFlow/Keras with IMU dataset
2. Convert to TFLite:
```python
import tensorflow as tf

# Load your trained model
model = tf.keras.models.load_model('activity_model.h5')

# Convert to TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# Save
with open('activity_model.tflite', 'wb') as f:
    f.write(tflite_model)
```

3. Copy the `.tflite` file to this directory
