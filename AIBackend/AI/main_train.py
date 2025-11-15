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
        'HIEN': "/home/bnhan2710/source-code/PBL4/AI/dataset/HIEN",
        'TOAN': "/home/bnhan2710/source-code/PBL4/AI/dataset/TOAN",
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
        

        if 'UPSTAIRS' in activity_to_idx:
            class_weights_array[activity_to_idx['UPSTAIRS']] *= 3.0
        if 'DOWNSTAIRS' in activity_to_idx:
            class_weights_array[activity_to_idx['DOWNSTAIRS']] *= 5.0 
        if 'SITTING' in activity_to_idx:
            class_weights_array[activity_to_idx['SITTING']] *= 1.5
        if 'STANDING' in activity_to_idx:
            class_weights_array[activity_to_idx['STANDING']] *= 1.5
            
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

# ====================================================================
# PIPELINE HUẤN LUYỆN CUỐI CÙNG (FINAL MODEL TRAINING)
# ====================================================================

def train_final_model(test_subject_names, augmentation_config={'ratio_jitter': 0.5, 'ratio_warp': 0.25, 'ratio_scale': 0.25}):
    """
    Huấn luyện mô hình cuối cùng:
    - Chọn 2 người làm Test
    - Tất cả những người còn lại chia thành Training và Validation
    - Đưa ra kết quả đánh giá cuối cùng
    
    Args:
        test_subject_names: list of 2 subject names để làm test
        augmentation_config: dict cấu hình augmentation
    """
    print("\n" + "="*80)
    print("🎯 FINAL MODEL TRAINING - Training on Remaining Subjects, Testing on 2 Subjects")
    print("="*80)
    
    dataset_paths = {
        'HUNG': "/home/bnhan2710/source-code/PBL4/AI/dataset/HUNG",
        'BINH': "/home/bnhan2710/source-code/PBL4/AI/dataset/BINH",
        'NHAN': "/home/bnhan2710/source-code/PBL4/AI/dataset/NHAN",
        'CUONG': "/home/bnhan2710/source-code/PBL4/AI/dataset/CUONG",
        'PHONG': "/home/bnhan2710/source-code/PBL4/AI/dataset/PHONG",
        'BACH': "/home/bnhan2710/source-code/PBL4/AI/dataset/BACH",
        'HIEN': "/home/bnhan2710/source-code/PBL4/AI/dataset/HIEN",
        'TOAN': "/home/bnhan2710/source-code/PBL4/AI/dataset/TOAN",
    }
    
    loader = Preprocessor()
    unique_subjects = list(dataset_paths.keys())
    
    # Validate test subjects
    if not isinstance(test_subject_names, list) or len(test_subject_names) != 2:
        raise ValueError("test_subject_names must be a list of 2 subject names!")
    
    for test_subject in test_subject_names:
        if test_subject not in unique_subjects:
            raise ValueError(f"Test subject '{test_subject}' not found in dataset!")
    
    # Chọn validation subject từ những người còn lại
    remaining_subjects = [s for s in unique_subjects if s not in test_subject_names]
    val_subject_name = remaining_subjects[0]  # Lấy subject đầu tiên còn lại làm validation
    train_subjects = [s for s in remaining_subjects if s != val_subject_name]
    
    print(f"\n📂 Final Model Configuration:")
    print(f"  Test Subjects (2): {test_subject_names}")
    print(f"  Validation Subject: {val_subject_name}")
    print(f"  Training Subjects ({len(train_subjects)}): {train_subjects}")
    
    # 1. Chuẩn bị dữ liệu
    print(f"\n📊 Loading and preparing data...")
    
    # Load dữ liệu cho từng subject
    all_data = {}
    for subject_name in unique_subjects:
        try:
            subject_df, activity_counts = loader.load_single_dataset(dataset_paths[subject_name], subject_name)
            if subject_df is not None:
                all_data[subject_name] = subject_df
                print(f"  ✅ Loaded {subject_name}: {len(subject_df)} samples")
        except Exception as e:
            print(f"  ❌ Error loading {subject_name}: {e}")
    
    # Kiểm tra đủ subjects không
    if len(all_data) < 4:  # Cần ít nhất 4 subjects (2 test, 1 val, 1 train)
        raise ValueError(f"Not enough subjects! Need at least 4, but only have {len(all_data)}")
    
    # Tạo train/val/test splits
    print(f"\n🔄 Creating train/val/test splits...")
    
    # Combine test subjects
    test_dfs = [all_data[s] for s in test_subject_names if s in all_data]
    test_df = pd.concat(test_dfs, ignore_index=True)
    print(f"  Test set: {len(test_df)} samples from {test_subject_names}")
    
    # Validation subject
    val_df = all_data[val_subject_name]
    print(f"  Validation set: {len(val_df)} samples from {val_subject_name}")
    
    # Training subjects
    train_dfs = [all_data[s] for s in train_subjects if s in all_data]
    train_df = pd.concat(train_dfs, ignore_index=True)
    print(f"  Training set: {len(train_df)} samples from {train_subjects}")
    
    # Clean và process data
    train_df = loader.clean_data(train_df)
    val_df = loader.clean_data(val_df)
    test_df = loader.clean_data(test_df)
    
    # Balance training data
    train_df = loader.balance_dataset(train_df, method='smart_balance')
    
    # Create windows
    X_train, y_train, _ = loader.create_sliding_windows(train_df)
    X_val, y_val, _ = loader.create_sliding_windows(val_df)
    X_test, y_test, _ = loader.create_sliding_windows(test_df)
    
    # Normalize
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_train_reshaped = X_train.reshape(-1, X_train.shape[2])
    scaler.fit(X_train_reshaped)
    
    X_train = scaler.transform(X_train_reshaped).reshape(X_train.shape)
    X_val = scaler.transform(X_val.reshape(-1, X_val.shape[2])).reshape(X_val.shape)
    X_test = scaler.transform(X_test.reshape(-1, X_test.shape[2])).reshape(X_test.shape)
    
    print(f"\n✅ Data prepared:")
    print(f"  Train: {X_train.shape}")
    print(f"  Val: {X_val.shape}")
    print(f"  Test: {X_test.shape}")
    
    # 2. Data Augmentation
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
    
    # Boost weights cho các lớp khó
    if 'UPSTAIRS' in activity_to_idx:
        class_weights_array[activity_to_idx['UPSTAIRS']] *= 3.0
    if 'DOWNSTAIRS' in activity_to_idx:
        class_weights_array[activity_to_idx['DOWNSTAIRS']] *= 5.0
    if 'SITTING' in activity_to_idx:
        class_weights_array[activity_to_idx['SITTING']] *= 1.5
    if 'STANDING' in activity_to_idx:
        class_weights_array[activity_to_idx['STANDING']] *= 1.5
    
    class_weights = dict(enumerate(class_weights_array))
    print(f"\n⚖️ Class Weights: {np.round(class_weights_array, 2)}")
    
    # 4. Xây dựng mô hình
    print(f"\n🏗️ Building Final CNN-GRU Model...")
    tf.keras.backend.clear_session()
    model = create_model_cnn_gru(
        timesteps=loader.window_size,
        n_features=X_train.shape[2],
        n_classes=loader.n_classes
    )
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.0005),
        loss=weighted_categorical_crossentropy(class_weights_array),
        metrics=['accuracy']
    )
    
    print(f"\n📋 Model Summary:")
    model.summary()
    
    # 5. Callbacks
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
            f'final_model_test_{"_".join(test_subject_names)}.h5',
            monitor='val_loss',
            save_best_only=True,
            verbose=1,
            mode='min'
        )
    ]
    
    # 6. Training
    print(f"\n🚀 Starting Final Model Training...")
    print("-" * 80)
    history = model.fit(
        X_train, y_train_cat,
        validation_data=(X_val, y_val_cat),
        epochs=100,
        batch_size=16,
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=1
    )
    
    # 7. Load best weights và đánh giá
    model_filename = f'final_model_test_{"_".join(test_subject_names)}.h5'
    print(f"\n📊 Evaluating Final Model on Test Subjects: {', '.join(test_subject_names)}")
    try:
        model.load_weights(model_filename)
        print(f"  ✅ Loaded best weights from checkpoint")
    except Exception as e:
        print(f"  ⚠️ Could not load best weights: {e}")
    
    test_results = model.evaluate(X_test, y_test_cat, verbose=0)
    test_loss, test_accuracy = test_results
    
    y_pred = model.predict(X_test, verbose=0)
    y_pred_classes = np.argmax(y_pred, axis=1)
    y_true_classes = np.argmax(y_test_cat, axis=1)
    
    f1 = f1_score(y_true_classes, y_pred_classes, average='weighted')
    cm = confusion_matrix(y_true_classes, y_pred_classes)
    
    # 8. Kết quả chi tiết
    print("\n" + "="*80)
    print("🎯 FINAL MODEL RESULTS")
    print("="*80)
    print(f"Test Subjects: {', '.join(test_subject_names)}")
    print(f"Test Loss: {test_loss:.4f}")
    print(f"Test Accuracy: {test_accuracy:.4f}")
    print(f"Weighted F1-Score: {f1:.4f}")
    print("\n" + classification_report(y_true_classes, y_pred_classes, 
                                      target_names=loader.activity_names, digits=4))
    
    # 9. Visualizations
    test_str = "_".join(test_subject_names)
    plot_training_history(history, test_str, val_subject_name, 0, file_suffix="final_model")
    plot_single_cm(cm, loader.activity_names, test_str, 0, file_suffix="final_model")
    
    # 10. Lưu kết quả
    final_results = {
        'test_subjects': test_subject_names,
        'test_accuracy': test_accuracy,
        'weighted_f1': f1,
        'test_loss': test_loss,
        'confusion_matrix': cm,
        'training_history': history.history,
        'class_weights': class_weights_array
    }
    
    print(f"\n💾 Final model saved as: {model_filename}")
    print("="*80)
    
    return final_results, model

if __name__ == "__main__":
    
    # Cấu hình Augmentation
    AUGMENTATION_CONFIG = {
        'ratio_jitter': 0.5, 
        'ratio_warp': 0.25, 
        'ratio_scale': 0.25
    }
    
    # ============================================================
    # BƯỚC 1: LOSO Cross-Validation (Đánh giá khả năng tổng quát)
    # ============================================================
    # print("\n" + "="*80)
    # print("PHASE 1: LOSO CROSS-VALIDATION")
    # print("="*80)
    # loso_results = train_model_loso_cnn_gru_aug(augmentation_config=AUGMENTATION_CONFIG)
    
    # ============================================================
    # BƯỚC 2: Huấn luyện mô hình cuối cùng
    # ============================================================
    print("\n" + "="*80)
    print("PHASE 2: FINAL MODEL TRAINING")
    print("="*80)
    
    # Chọn 2 subjects để test
    test_subjects = ['HIEN', 'PHONG']
    print(f"\n🎯 Selected test subjects: {', '.join(test_subjects)}")
    
    final_results, final_model = train_final_model(
        test_subject_names=test_subjects,
        augmentation_config=AUGMENTATION_CONFIG
    )
    
    # ============================================================
    # BƯỚC 3: So sánh kết quả LOSO vs Final Model
    # ============================================================
    # if loso_results and final_results:
    #     print("\n" + "="*80)
    #     print("📊 COMPARISON: LOSO vs FINAL MODEL")
    #     print("="*80)
        
    #     print(f"\nTest Subjects: {', '.join(test_subjects)}")
        
    #     # So sánh với LOSO results của các test subjects
    #     for test_subj in test_subjects:
    #         loso_subject_result = next((r for r in loso_results if r['test_subject'] == test_subj), None)
            
    #         if loso_subject_result:
    #             print(f"\n{test_subj}:")
    #             print(f"  LOSO Accuracy: {loso_subject_result['test_accuracy']:.4f}")
    #             print(f"  LOSO F1-Score: {loso_subject_result['weighted_f1']:.4f}")
        
    #     print(f"\nFinal Model (2 test subjects combined):")
    #     print(f"  Accuracy: {final_results['test_accuracy']:.4f}")
    #     print(f"  F1-Score: {final_results['weighted_f1']:.4f}")
        
    #     print("\n" + "="*80)
    #     print("✅ TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
    #     print("="*80)