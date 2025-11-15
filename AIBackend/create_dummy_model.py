import tensorflow as tf
import numpy as np
import os

print("Creating dummy model for testing...")

# Create simple model
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(40, 11)),
    tf.keras.layers.LSTM(64, return_sequences=True),
    tf.keras.layers.LSTM(32),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(6, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

print("Model architecture:")
model.summary()

# Create directory if not exists
os.makedirs('AI/models', exist_ok=True)

# Save model
model.save('AI/models/best_model.h5')
print("\n✅ Dummy model saved to AI/models/best_model.h5")

# Test load
print("\nTesting load...")
loaded_model = tf.keras.models.load_model('AI/models/best_model.h5', compile=False)
print("✅ Model loaded successfully")

# Test prediction
print("\nTesting prediction...")
test_input = np.random.randn(1, 40, 11)
prediction = loaded_model.predict(test_input, verbose=0)
print(f"Prediction shape: {prediction.shape}")
print(f"Predicted class: {np.argmax(prediction[0])}")
print(f"Probabilities: {prediction[0]}")

print("\n✅ All tests passed!")
