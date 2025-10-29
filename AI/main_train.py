import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix, f1_score

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

import os
import warnings
warnings.filterwarnings('ignore')

from src.preprocessing import Preprocessor
from src.model import create_model_cnn_gru, weighted_categorical_crossentropy
from src.augmentation import augment_data_improved
from src.utils import plot_training_history, plot_single_cm, plot_loso_results

# Đảm bảo Tensorflow sử dụng GPU nếu có
try:
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    print(f"TensorFlow found GPUs: {len(gpus)}")
except Exception as e:
    print(f"Error configuring GPU: {e}")

# ====================================================================
# HÀM HUẤN LUYỆN CHÍNH (CÁCH 1: CNN-GRU + AUGMENTATION)
# ====================================================================

def train_model_loso_cnn_gru_aug(augmentation_config={'ratio_jitter': 0.5, 'ratio_warp': 0.25, 'ratio_scale': 0.25}):
    
    print("🚀 Starting HAR Model Training with LOSO Cross-Validation (CNN-GRU, Improved Augmentation)")
    print("="*80)
    
    dataset_paths = {
        'HUNG': "/home/bnhan2710/source-code/PBL4/AI/dataset/HUNG",
        'BINH': "/home/bnhan2710/source-code/PBL4/AI/dataset/BINH",
        'NHAN': "/home/bnhan2710/source-code/PBL4/AI/dataset/NHAN",
        'CUONG': "/home/bnhan2710/source-code/PBL4/AI/dataset/CUONG",
        'PHONG': "/home/bnhan2710/source-code/PBL4/AI/dataset/PHONG",
        'BACH': "/home/bnhan2710/source-code/PBL4/AI/dataset/BACH",
    }
    
    loader = Preprocessor()
    unique_subjects = list(dataset_paths.keys())
    all_test_metrics = []
    total_cm = np.zeros((loader.n_classes, loader.n_classes), dtype=int)
    file_suffix = "cnn_gru_aug" # Định danh cho kết quả
    
    for fold_idx, test_subject in enumerate(unique_subjects):
        
        print(f"\n\n================ FOLD {fold_idx + 1}/{len(unique_subjects)}: TEST SUBJECT = {test_subject} ================")
        
        remaining_subjects = [s for s in unique_subjects if s != test_subject]
        # Chọn ngẫu nhiên (hoặc luân phiên) một người còn lại làm Validation Subject
        val_subject = remaining_subjects[fold_idx % len(remaining_subjects)] 
        
        print(f"  Validation Subject for this fold: {val_subject}")

        # 1. Chuẩn bị Dữ liệu (feature_extraction=False cho dữ liệu chuỗi thời gian)
        try:
            X_train, X_val, X_test, y_train, y_val, y_test, scaler = loader.prepare_data(
                dataset_paths,
                feature_extraction=False,
                test_subject_name=test_subject,  
                val_subject_name=val_subject
            )
        except ValueError as e:
            print(f"  Skipping fold {test_subject} due to error: {e}")
            continue
        
        # 2. ÁP DỤNG DATA AUGMENTATION CẢI TIẾN
        print(f"\n✨ Augmenting Training Data (Current size: {len(X_train)})")
        X_train, y_train = augment_data_improved(X_train, y_train, **augmentation_config)
        print(f"    New Training size: {len(X_train)}")
            
        y_train_cat = to_categorical(y_train, num_classes=loader.n_classes)
        y_val_cat = to_categorical(y_val, num_classes=loader.n_classes)
        y_test_cat = to_categorical(y_test, num_classes=loader.n_classes)
        
        # 3. Tính Class Weights
        unique_classes = np.unique(y_train)
        class_weights_array = compute_class_weight(
            class_weight='balanced',
            classes=unique_classes,
            y=y_train
        )
        activity_to_idx = {name: idx for idx, name in enumerate(loader.activity_names)}
        
        # Tăng cường trọng số cho các hoạt động khó
        if 'UPSTAIRS' in activity_to_idx:
            class_weights_array[activity_to_idx['UPSTAIRS']] *= 1.5
        if 'DOWNSTAIRS' in activity_to_idx:
            class_weights_array[activity_to_idx['DOWNSTAIRS']] *= 3.0 
            
        class_weights = dict(enumerate(class_weights_array))
        
        print(f"  Class Weights (Index: {list(activity_to_idx.keys())}): {np.round(class_weights_array, 2)}")


        # 4. Xây dựng và Biên dịch Mô hình CNN-GRU (chống quá khớp cao)
        tf.keras.backend.clear_session() 
        model = create_model_cnn_gru(
            timesteps=loader.window_size,
            n_features=X_train.shape[2],
            n_classes=loader.n_classes
        )
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),  
            loss=weighted_categorical_crossentropy(class_weights_array),
            metrics=['accuracy']
        )
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=30, 
                restore_best_weights=True,
                verbose=1,
                mode='min'
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,  
                patience=10, 
                min_lr=1e-8,
                verbose=1,
                mode='min'
            ),
            ModelCheckpoint(
                f'best_model_{file_suffix}_fold_{test_subject}.h5',
                monitor='val_loss',
                save_best_only=True,
                verbose=0,
                mode='min'
            )
        ]
        
        # 5. Huấn luyện 
        print(f"  Starting training for fold {fold_idx + 1}...")
        history = model.fit(
            X_train, y_train_cat,
            validation_data=(X_val, y_val_cat),
            epochs=50,
            batch_size=16, 
            callbacks=callbacks,
            class_weight=class_weights,
            verbose=0
        )
        
        # VẼ LỊCH SỬ HUẤN LUYỆN
        plot_training_history(history, test_subject, val_subject, fold_idx, file_suffix=file_suffix)

        # 6. Đánh giá trên tập Test
        try:
            model.load_weights(f'best_model_{file_suffix}_fold_{test_subject}.h5') 
        except Exception as e:
             print(f"  Warning: Could not load best weights for {test_subject}. Using current epoch's weights.")
             
        test_results = model.evaluate(X_test, y_test_cat, verbose=0)
        test_loss, test_accuracy = test_results
        
        y_pred = model.predict(X_test, verbose=0)
        y_pred_classes = np.argmax(y_pred, axis=1)
        y_true_classes = np.argmax(y_test_cat, axis=1)
        
        f1 = f1_score(y_true_classes, y_pred_classes, average='weighted')
        cm = confusion_matrix(y_true_classes, y_pred_classes)
        total_cm += cm 
        
        print(f"\n  Fold {fold_idx + 1} Results (Subject {test_subject}):")
        print(f"    Test Loss: {test_loss:.4f}")
        print(f"    Test Accuracy: {test_accuracy:.4f}")
        print(f"    Weighted F1-Score: {f1:.4f}")
        print(classification_report(y_true_classes, y_pred_classes, 
                               target_names=loader.activity_names, digits=4))

        # VẼ CONFUSION MATRIX CHO TỪNG NGƯỜI
        plot_single_cm(cm, loader.activity_names, test_subject, fold_idx, file_suffix=file_suffix)

        all_test_metrics.append({
            'test_subject': test_subject,
            'test_accuracy': test_accuracy,
            'weighted_f1': f1,
            'test_loss': test_loss,
            'confusion_matrix': cm
        })
    
    # 7. Báo cáo Kết quả Cuối cùng
    print("\n" + "="*80)
    print(" LOSO CROSS-VALIDATION FINAL SUMMARY (CNN-GRU + IMPROVED AUGMENTATION)")
    print("="*80)
    
    avg_accuracy = np.mean([m['test_accuracy'] for m in all_test_metrics])
    avg_f1 = np.mean([m['weighted_f1'] for m in all_test_metrics])
    avg_loss = np.mean([m['test_loss'] for m in all_test_metrics])
    
    print(f" Total Folds: {len(unique_subjects)}")
    print(f" Average Test Loss: {avg_loss:.4f}")
    print(f" Average Test Accuracy: {avg_accuracy:.4f}")
    print(f" Average Weighted F1-Score: {avg_f1:.4f}")
    
    # Visualization
    plot_loso_results(all_test_metrics, loader.activity_names, total_cm, file_suffix=file_suffix)

    return all_test_metrics

if __name__ == "__main__":
    
    # Cấu hình Augmentation
    AUGMENTATION_CONFIG = {
        'ratio_jitter': 0.5, 
        'ratio_warp': 0.25, 
        'ratio_scale': 0.25
    }
    
    # Bắt đầu quá trình huấn luyện
    results = train_model_loso_cnn_gru_aug(augmentation_config=AUGMENTATION_CONFIG)