import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, regularizers
import numpy as np

def create_model_cnn_gru(timesteps=40, n_features=11, n_classes=6):
    L2_REG = 0.005  # Giúp giảm overfitting bằng cách phạt các trọng số quá lớn (L2 regularization)
    
    # ======================
    # Đầu vào (Input Layer)
    # ======================
    inputs = layers.Input(shape=(timesteps, n_features), name='imu_input')
    
    # ======================
    # CNN Block 1 – Trích xuất đặc trưng cục bộ
    # ======================
    x = layers.Conv1D(
        filters=64,                
        kernel_size=5,            
        activation='relu',
        padding='same',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='conv1d_1'
    )(inputs)
    x = layers.LayerNormalization(name='ln_1')(x) 
    x = layers.MaxPooling1D(pool_size=2, name='maxpool_1')(x)  
    x = layers.Dropout(0.4, name='dropout_1')(x)  
    
    # ======================
    #  CNN Block 2 – Đặc trưng sâu hơn
    # ======================
    x = layers.Conv1D(
        filters=96,
        kernel_size=5,
        activation='relu',
        padding='same',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='conv1d_2'
    )(x)
    x = layers.LayerNormalization(name='ln_2')(x)
    x = layers.MaxPooling1D(pool_size=2, name='maxpool_2')(x)
    x = layers.Dropout(0.4, name='dropout_2')(x)
    
    # ======================
    #  GRU Layer – Học phụ thuộc theo thời gian
    # ======================
    # GRU: Gated Recurrent Unit 
    x = layers.GRU(
        units=64, 
        return_sequences=False,  # Chỉ lấy output cuối cùng (thay vì toàn bộ chuỗi)
        kernel_regularizer=regularizers.l2(L2_REG),
        recurrent_regularizer=regularizers.l2(L2_REG),
        dropout=0.4,              # Dropout trên input connections
        recurrent_dropout=0.3,    # Dropout trên recurrent state
        name='gru_layer'
    )(x)
    
    x = layers.LayerNormalization(name='ln_gru')(x)
    x = layers.Dropout(0.5, name='dropout_gru_final')(x)
    
    # ======================
    # Dense Block – Phân loại
    # ======================
    # Dense 1: kết hợp các đặc trưng trích xuất từ CNN + GRU
    x = layers.Dense(
        96,
        activation='relu',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='dense_1'
    )(x)
    x = layers.Dropout(0.5, name='dropout_dense_1')(x)
    
    # Dense 2: giảm chiều, học đặc trưng phức tạp hơn
    x = layers.Dense(
        64,
        activation='relu',
        kernel_regularizer=regularizers.l2(L2_REG),
        name='dense_2'
    )(x)
    x = layers.Dropout(0.4, name='dropout_dense_2')(x)
    
    # ======================
    #  Output Layer – Dự đoán lớp hoạt động
    # ======================
    outputs = layers.Dense(
        n_classes,
        activation='softmax',    
        kernel_regularizer=regularizers.l2(L2_REG),
        name='output'
    )(x)
    
    model = models.Model(inputs=inputs, outputs=outputs, name='CNN_GRU_Simplified')
    
    return model


# ======================
#  Weighted Categorical Crossentropy
# ======================
def weighted_categorical_crossentropy(weights):
    weights = tf.constant(weights, dtype=tf.float32)
    
    def loss(y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, tf.keras.backend.epsilon(), 1 - tf.keras.backend.epsilon())
        loss = -y_true * tf.math.log(y_pred)   # Cross Entropy cơ bản
        weighted_loss = loss * weights         # Áp dụng trọng số từng lớp
        return tf.reduce_mean(tf.reduce_sum(weighted_loss, axis=-1))
    
    return loss

