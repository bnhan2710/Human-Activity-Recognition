import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.utils.class_weight import compute_class_weight
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, regularizers
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.append('/home/bnhan2710/source-code/PBL4/AI')
from preprocessor.preprocessor import Preprocessor


def create_model(timesteps=20, n_features=9, n_classes=6):

    inputs = layers.Input(shape=(timesteps, n_features), name='imu_input')
    
    # ============ CNN Block - Feature Extraction ============
    # Lớp CNN đầu tiên để trích xuất đặc trưng cơ bản
    x = layers.Conv1D(
        filters=32,
        kernel_size=3,
        activation='relu',
        padding='same',
        kernel_regularizer=regularizers.l2(0.003), 
        name='conv1d_1'
    )(inputs)

    # Lớp BatchNorm và MaxPooling để giảm nhiễu và giảm kích thước
    x = layers.BatchNormalization(name='bn_1')(x)
    x = layers.MaxPooling1D(pool_size=2, name='maxpool_1')(x)

    # Dropout để tránh overfitting
    x = layers.Dropout(0.3, name='dropout_1')(x) 
    
    # Lớp CNN thứ hai để trích xuất đặc trưng phức tạp hơn
    x = layers.Conv1D(
        filters=64,  
        kernel_size=3,
        activation='relu',
        padding='same',
        kernel_regularizer=regularizers.l2(0.003),
        name='conv1d_2'
    )(x)

    x = layers.BatchNormalization(name='bn_2')(x)
    x = layers.Dropout(0.3, name='dropout_2')(x)  
    
    # ============ GRU Block - Temporal Dependencies ============
    x = layers.GRU(
        units=32,  
        return_sequences=False,
        kernel_regularizer=regularizers.l2(0.003),
        recurrent_regularizer=regularizers.l2(0.003),
        dropout=0.2,  
        recurrent_dropout=0.2,  
        name='gru'
    )(x)

    x = layers.BatchNormalization(name='bn_gru')(x)
    x = layers.Dropout(0.4, name='dropout_gru')(x)  
    
    # ============ Dense Block - Classification ============
    x = layers.Dense(
        64,  
        activation='relu',
        kernel_regularizer=regularizers.l2(0.003),
        name='dense'
    )(x)
    x = layers.Dropout(0.4, name='dropout_dense')(x)  
    
    # Output layer
    outputs = layers.Dense(
        n_classes,
        activation='softmax',
        kernel_regularizer=regularizers.l2(0.003),
        name='output'
    )(x)
    
    model = models.Model(inputs=inputs, outputs=outputs, name='CNN_GRU')
    
    return model


def weighted_categorical_crossentropy(weights):
    """Weighted CCE for handling class imbalance"""
    weights = tf.constant(weights, dtype=tf.float32)
    
    def loss(y_true, y_pred):
        # Clip predictions to prevent log(0)
        y_pred = tf.clip_by_value(y_pred, tf.keras.backend.epsilon(), 1 - tf.keras.backend.epsilon())
        
        # Calculate categorical crossentropy
        loss = -y_true * tf.math.log(y_pred)
        
        # Apply class weights
        weighted_loss = loss * weights
        
        return tf.reduce_mean(tf.reduce_sum(weighted_loss, axis=-1))
    
    return loss

# ============ MAIN TRAINING FUNCTION ============
def train_model():
    print(" Starting HAR Model Training")
    print("="*70)
    
    # Load data
    print("🚀 Loading and preparing combined dataset...")
    loader = Preprocessor()
    
    # Define paths to all datasets
    dataset_paths = {
        'HUNG': "/home/bnhan2710/source-code/PBL4/AI/dataset/HUNG",
        'BINH': "/home/bnhan2710/source-code/PBL4/AI/dataset/BINH",
        'NHAN': "/home/bnhan2710/source-code/PBL4/AI/dataset/NHAN",
        'BACH': "/home/bnhan2710/source-code/PBL4/AI/dataset/BACH",
    }
    
    X_train, X_val, X_test, y_train, y_val, y_test, scaler = loader.prepare_data(dataset_paths)
    
    #  OPTION 1: Try WITHOUT augmentation first
    # print("\n⚠️ Testing WITHOUT augmentation first...")
    X_train_aug, y_train_aug = X_train, y_train
    
    #  OPTION 2: Or use light augmentation (uncomment if needed)
    # X_train_aug, y_train_aug = safe_imu_augmentation(
    #     X_train, y_train, 
    #     augment_factor=1.3,
    #     activity_names=loader.activity_names
    # )
    
    print(f"\n📊 Final Dataset Summary:")
    print(f"  Training: {X_train_aug.shape}")
    print(f"  Validation: {X_val.shape}")
    print(f"  Test: {X_test.shape}")
    
    # Convert to categorical
    y_train_cat = to_categorical(y_train_aug, num_classes=loader.n_classes)
    y_val_cat = to_categorical(y_val, num_classes=loader.n_classes)
    y_test_cat = to_categorical(y_test, num_classes=loader.n_classes)
    
    # Compute class weights
    unique_classes = np.unique(y_train_aug)
    class_weights_array = compute_class_weight(
        class_weight='balanced',
        classes=unique_classes,
        y=y_train_aug
    )
    
    # Boost weights for UPSTAIRS/DOWNSTAIRS (often confused with WALKING)
    activity_to_idx = {name: idx for idx, name in enumerate(loader.activity_names)}
    
    if 'UPSTAIRS' in activity_to_idx:
        upstairs_idx = activity_to_idx['UPSTAIRS']
        class_weights_array[upstairs_idx] *= 1.5
    
    if 'DOWNSTAIRS' in activity_to_idx:
        downstairs_idx = activity_to_idx['DOWNSTAIRS']
        class_weights_array[downstairs_idx] *= 1.5  
    
    class_weights = dict(enumerate(class_weights_array))
    
    print(f"\n⚖️ Adjusted Class Weights:")
    for cls, weight in class_weights.items():
        print(f"  Class {loader.activity_names[cls]}: {weight:.2f}")
    
    print(f"\n Building  CNN-GRU Model...")
    model = create_model(
        timesteps=loader.window_size,
        n_features=loader.n_features,
        n_classes=loader.n_classes
    )
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),  
        loss=weighted_categorical_crossentropy(class_weights_array),
        metrics=['accuracy']
    )
    
    print("\n📋 Model Summary:")
    model.summary()
    
    # Print model parameters
    total_params = model.count_params()
    print(f"\n📊 Model Parameters: {total_params:,}")
    
    # Enhanced callbacks
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=25,
            restore_best_weights=True,
            verbose=1,
            mode='min',
            min_delta=0.001
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,  
            patience=10,
            min_lr=1e-7,
            verbose=1,
            mode='min'
        ),
        ModelCheckpoint(
            'best_model.h5',
            monitor='val_loss',
            save_best_only=True,
            verbose=1,
            mode='min'
        )
    ]
    
    print("\n🏋️ Starting Training...")
    print("-" * 70)
    
    # Train with class weights
    history = model.fit(
        X_train_aug, y_train_cat,
        validation_data=(X_val, y_val_cat),
        epochs=20,
        batch_size=32,  
        callbacks=callbacks,
        # class_weight=class_weights,
        verbose=1
    )
    
    print("\n" + "="*70)
    print(" EVALUATING MODEL PERFORMANCE")
    print("="*70)
    
    # Evaluate on test set
    test_results = model.evaluate(X_test, y_test_cat, verbose=0)
    test_loss, test_accuracy = test_results
    
    y_pred = model.predict(X_test, verbose=0)
    y_pred_classes = np.argmax(y_pred, axis=1)
    y_true_classes = np.argmax(y_test_cat, axis=1)
    
    print(f"\n Test Results:")
    print(f"  Test Loss: {test_loss:.4f}")
    print(f"  Test Accuracy: {test_accuracy:.4f}")
    
    f1 = f1_score(y_true_classes, y_pred_classes, average='weighted')
    print(f"  Weighted F1-Score: {f1:.4f}")
    
    # Classification report
    print(f"\n Classification Report:")
    print(classification_report(y_true_classes, y_pred_classes, 
                               target_names=loader.activity_names, digits=4))
    
    cm = confusion_matrix(y_true_classes, y_pred_classes)
    
    # Visualization
    plt.figure(figsize=(18, 10))
    
    # Accuracy plot
    plt.subplot(2, 3, 1)
    plt.plot(history.history['accuracy'], label='Train Accuracy', color='blue', alpha=0.8, linewidth=2)
    plt.plot(history.history['val_accuracy'], label='Val Accuracy', color='orange', alpha=0.8, linewidth=2)
    plt.axhline(y=test_accuracy, color='red', linestyle='--', label=f'Test: {test_accuracy:.3f}', linewidth=2)
    plt.title('Model Accuracy', fontweight='bold', fontsize=12)
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Loss plot
    plt.subplot(2, 3, 2)
    plt.plot(history.history['loss'], label='Train Loss', color='blue', alpha=0.8, linewidth=2)
    plt.plot(history.history['val_loss'], label='Val Loss', color='orange', alpha=0.8, linewidth=2)
    plt.axhline(y=test_loss, color='red', linestyle='--', label=f'Test: {test_loss:.3f}', linewidth=2)
    plt.title('Model Loss', fontweight='bold', fontsize=12)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Confusion Matrix
    plt.subplot(2, 3, 3)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=loader.activity_names, 
                yticklabels=loader.activity_names,
                cbar_kws={'label': 'Count'})
    plt.title('Confusion Matrix', fontweight='bold', fontsize=12)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # Normalized Confusion Matrix
    plt.subplot(2, 3, 4)
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    sns.heatmap(cm_normalized, annot=True, fmt='.2f', cmap='RdYlGn', 
                xticklabels=loader.activity_names, 
                yticklabels=loader.activity_names,
                cbar_kws={'label': 'Proportion'}, vmin=0, vmax=1)
    plt.title('Normalized Confusion Matrix', fontweight='bold', fontsize=12)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # Train-Val Gap
    plt.subplot(2, 3, 5)
    gap = np.array(history.history['accuracy']) - np.array(history.history['val_accuracy'])
    plt.plot(gap, color='red', label='Accuracy Gap', linewidth=2)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.axhline(y=0.1, color='orange', linestyle='--', alpha=0.5, label='Warning (10%)')
    plt.axhline(y=0.15, color='red', linestyle='--', alpha=0.5, label='Critical (15%)')
    plt.fill_between(range(len(gap)), gap, 0, where=(gap > 0), alpha=0.3, color='red')
    plt.title('Train-Val Accuracy Gap', fontweight='bold', fontsize=12)
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy Difference')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Per-class accuracy
    plt.subplot(2, 3, 6)
    class_accuracies = []
    for i in range(len(loader.activity_names)):
        mask = y_true_classes == i
        if np.sum(mask) > 0:
            acc = np.mean(y_pred_classes[mask] == y_true_classes[mask])
            class_accuracies.append(acc)
        else:
            class_accuracies.append(0)
    
    colors = ['green' if acc > 0.7 else 'orange' if acc > 0.5 else 'red' for acc in class_accuracies]
    bars = plt.bar(range(len(loader.activity_names)), class_accuracies, color=colors, alpha=0.7)
    plt.xlabel('Activity')
    plt.ylabel('Accuracy')
    plt.title('Per-class Accuracy', fontweight='bold', fontsize=12)
    plt.xticks(range(len(loader.activity_names)), loader.activity_names, rotation=45, ha='right')
    plt.axhline(y=0.7, color='green', linestyle='--', alpha=0.3, label='Good (>70%)')
    plt.axhline(y=0.5, color='orange', linestyle='--', alpha=0.3, label='Fair (>50%)')
    plt.ylim(0, 1.0)
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, (bar, acc) in enumerate(zip(bars, class_accuracies)):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{acc:.2f}',
                ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('../results/training_results.png', dpi=300, bbox_inches='tight')
    print("\n💾 Training visualization saved as training_results.png")
    plt.show()
    
    # Save model
    model.save('har_model.h5')
    print(" Model saved as har_model.h5")
    
    print(f"\n Detailed Per-class Performance:")
    print("="*70)
    for i, activity in enumerate(loader.activity_names):
        mask = y_true_classes == i
        if np.sum(mask) > 0:
            acc = np.mean(y_pred_classes[mask] == y_true_classes[mask])
            total_samples = np.sum(mask)
            correct = np.sum(y_pred_classes[mask] == y_true_classes[mask])
            
            confused_with = y_pred_classes[mask & (y_pred_classes != y_true_classes)]
            if len(confused_with) > 0:
                most_confused = np.bincount(confused_with).argmax()
                confusion_count = np.sum(confused_with == most_confused)
                confusion_pct = (confusion_count / total_samples) * 100
                print(f"  {activity:12s}: {acc:.4f} ({correct}/{total_samples}) "
                      f"- Most confused with {loader.activity_names[most_confused]} ({confusion_pct:.1f}%)")
            else:
                print(f"  {activity:12s}: {acc:.4f} ({correct}/{total_samples}) - Perfect!")
    
    return model, history, {
        'test_accuracy': test_accuracy,
        'test_loss': test_loss,
        'f1_score': f1,
        'confusion_matrix': cm,
        'per_class_accuracy': class_accuracies,
        'classification_report': classification_report(
            y_true_classes, y_pred_classes, 
            target_names=loader.activity_names, 
            output_dict=True
        )
    }

if __name__ == "__main__":
    trained_model, training_history, eval_metrics = train_model()