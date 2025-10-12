import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
import numpy as np
import sys
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import time
# Try to import activity names from test/models with robust sys.path handling
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from test.models.activity_encoding import get_activity_list as _get_activity_list
    CLASS_NAMES = _get_activity_list()
    N_CLASSES = len(CLASS_NAMES)
except Exception:
    # Fallback to a default 5-class set if helper is unavailable
    CLASS_NAMES = ['Walking', 'Running', 'Sitting', 'Standing', 'Jumping']
    N_CLASSES = len(CLASS_NAMES)


class BaselineCNN:
    """
    Baseline 1D CNN model for Human Activity Recognition
    Pure CNN without RNN components for comparison with Hybrid CNN-GRU
    """
    
    def __init__(self, timesteps=100, n_features=6, n_classes=5):
        """
        Args:
            timesteps: Window size (100 samples @ 20Hz = 5 seconds)
            n_features: 6 channels (Acc_x, Acc_y, Acc_z, Gyro_x, Gyro_y, Gyro_z)
            n_classes: Number of activity classes
        """
        self.timesteps = timesteps
        self.n_features = n_features
        self.n_classes = n_classes
        self.model = None
        self.history = None
        
    def build_model(self, filters=[64, 32], kernel_size=3, dense_units=64):
        """
        Build 1D CNN architecture
        
        Architecture:
        Input (100, 6)
        -> Conv1D Block 1 (feature extraction)
        -> Conv1D Block 2 (feature extraction)
        -> Global Average Pooling (dimension reduction)
        -> Dense Block (classification)
        -> Softmax Output
        
        Args:
            filters: List of filter sizes for each conv layer [64, 32]
            kernel_size: Size of convolution kernel
            dense_units: Units in dense layer
        """
        inputs = layers.Input(shape=(self.timesteps, self.n_features), 
                            name='imu_input')
        
        x = inputs
        
        # ============ Conv1D Blocks ============
        for i, f in enumerate(filters):
            x = layers.Conv1D(
                filters=f, 
                kernel_size=kernel_size, 
                activation='relu',
                padding='same',
                name=f'conv1d_{i+1}'
            )(x)
            x = layers.BatchNormalization(name=f'bn_{i+1}')(x)
            x = layers.MaxPooling1D(pool_size=2, name=f'maxpool_{i+1}')(x)
            x = layers.Dropout(0.3, name=f'dropout_conv_{i+1}')(x)
        
        # ============ Global Pooling ============
        # Reduce temporal dimension to single vector
        x = layers.GlobalAveragePooling1D(name='global_avg_pool')(x)
        
        # ============ Dense Block ============
        x = layers.Dense(dense_units, activation='relu', name='dense_1')(x)
        x = layers.Dropout(0.4, name='dropout_dense')(x)
        
        # Output layer
        outputs = layers.Dense(self.n_classes, activation='softmax', name='output')(x)
        
        # Create model
        self.model = models.Model(inputs=inputs, outputs=outputs, name='Baseline_1D_CNN')
        
        return self.model
    
    def compile_model(self, learning_rate=0.001):
        """Compile model with optimizer and loss function"""
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        print(f"Model compiled with learning rate: {learning_rate}")
    
    def get_model_summary(self):
        """Print model architecture"""
        return self.model.summary()
    
    def count_parameters(self):
        """Count total and trainable parameters"""
        trainable = np.sum([np.prod(v.shape) for v in self.model.trainable_weights])
        non_trainable = np.sum([np.prod(v.shape) for v in self.model.non_trainable_weights])
        total = trainable + non_trainable
        
        print(f"\nTotal parameters: {total:,}")
        print(f"Trainable parameters: {trainable:,}")
        print(f"Non-trainable parameters: {non_trainable:,}")
        
        return total, trainable, non_trainable
    
    def train(self, X_train, y_train, X_val, y_val, epochs=100, batch_size=32, verbose=1):
        """
        Train the model
        
        Args:
            X_train: Training data (n_samples, timesteps, n_features)
            y_train: Training labels (n_samples,)
            X_val: Validation data
            y_val: Validation labels
            epochs: Maximum number of epochs
            batch_size: Batch size for training
            verbose: Verbosity mode
        """
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=8,
                min_lr=1e-6,
                verbose=1
            )
        ]
        
        print(f"\nStarting training for {epochs} epochs...")
        start_time = time.time()
        
        # Train
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        training_time = time.time() - start_time
        print(f"\nTraining completed in {training_time:.2f} seconds")
        
        return self.history
    
    def evaluate(self, X_test, y_test):
        """Evaluate model on test data"""
        test_loss, test_acc = self.model.evaluate(X_test, y_test, verbose=0)
        print(f"\n{'='*50}")
        print(f"Test Loss: {test_loss:.4f}")
        print(f"Test Accuracy: {test_acc:.4f}")
        print(f"{'='*50}")
        
        return test_loss, test_acc
    
    def predict(self, X):
        """Make predictions"""
        return self.model.predict(X, verbose=0)
    
    def plot_training_history(self, save_path=None):
        """Plot training and validation metrics"""
        if self.history is None:
            print("No training history available. Train the model first.")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Accuracy plot
        ax1.plot(self.history.history['accuracy'], label='Train Accuracy', linewidth=2)
        ax1.plot(self.history.history['val_accuracy'], label='Val Accuracy', linewidth=2)
        ax1.set_xlabel('Epoch', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Accuracy', fontsize=12, fontweight='bold')
        ax1.set_title('CNN Model Accuracy', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Loss plot
        ax2.plot(self.history.history['loss'], label='Train Loss', linewidth=2)
        ax2.plot(self.history.history['val_loss'], label='Val Loss', linewidth=2)
        ax2.set_xlabel('Epoch', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Loss', fontsize=12, fontweight='bold')
        ax2.set_title('CNN Model Loss', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Training history plot saved to {save_path}")
        
        plt.show()
    
    def plot_confusion_matrix(self, X_test, y_test, class_names, save_path=None):
        """Plot confusion matrix"""
        y_pred = np.argmax(self.predict(X_test), axis=1)
        cm = confusion_matrix(y_test, y_pred)
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=class_names,
                   yticklabels=class_names,
                   cbar_kws={'label': 'Count'})
        plt.title('CNN Confusion Matrix', fontsize=14, fontweight='bold')
        plt.ylabel('True Label', fontsize=12, fontweight='bold')
        plt.xlabel('Predicted Label', fontsize=12, fontweight='bold')
        
        # Add accuracy to title
        acc = accuracy_score(y_test, y_pred)
        plt.suptitle(f'Overall Accuracy: {acc:.4f}', y=1.02, fontsize=12)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Confusion matrix saved to {save_path}")
        
        plt.show()
        
        # Print classification report
        print("\n" + "="*60)
        print("CLASSIFICATION REPORT")
        print("="*60)
        print(classification_report(y_test, y_pred, target_names=class_names))
    
    def save_model(self, filepath):
        """Save model to file"""
        self.model.save(filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load model from file"""
        self.model = keras.models.load_model(filepath)
        print(f"Model loaded from {filepath}")
    


# ============ Usage Example ============
def main():
    """Example usage of BaselineCNN"""
    
    print("\n" + "="*70)
    print(" BASELINE 1D CNN MODEL FOR HUMAN ACTIVITY RECOGNITION")
    print("="*70)
    
    # Generate dummy data for demonstration
    print("\nGenerating dummy data...")
    n_samples = 1000
    timesteps = 100
    n_features = 6
    # Determine number of classes from activity encoding helper (fallback to default)
    n_classes = N_CLASSES
    
    X = np.random.randn(n_samples, timesteps, n_features).astype(np.float32)
    y = np.random.randint(0, n_classes, n_samples)
    
    # Split data: 70% train, 15% validation, 15% test
    train_split = int(0.7 * n_samples)
    val_split = int(0.85 * n_samples)
    
    X_train, X_val, X_test = X[:train_split], X[train_split:val_split], X[val_split:]
    y_train, y_val, y_test = y[:train_split], y[train_split:val_split], y[val_split:]
    
    print(f"Train samples: {len(X_train)}")
    print(f"Validation samples: {len(X_val)}")
    print(f"Test samples: {len(X_test)}")
    
    # Create model
    print("\n" + "="*70)
    print("BUILDING MODEL")
    print("="*70)
    
    cnn_model = BaselineCNN(
        timesteps=timesteps, 
        n_features=n_features, 
        n_classes=n_classes
    )
    
    # Build with default parameters
    cnn_model.build_model(filters=[64, 32], kernel_size=3, dense_units=64)
    
    # Compile
    cnn_model.compile_model(learning_rate=0.001)
    
    # Show architecture
    print("\nModel Architecture:")
    cnn_model.get_model_summary()
    
    print("\nParameter Count:")
    cnn_model.count_parameters()
    
    # Train
    print("\n" + "="*70)
    print("TRAINING MODEL")
    print("="*70)
    
    history = cnn_model.train(
        X_train, y_train, 
        X_val, y_val, 
        epochs=50, 
        batch_size=32, 
        verbose=1
    )
    
    # Evaluate
    print("\n" + "="*70)
    print("EVALUATION ON TEST SET")
    print("="*70)
    
    test_loss, test_acc = cnn_model.evaluate(X_test, y_test)
    
    # Plot training history
    print("\nPlotting training history...")
    cnn_model.plot_training_history(save_path='cnn_training_history.png')
    
    # Plot confusion matrix
    # Use activity names from encoding helper for plots and reports
    class_names = CLASS_NAMES
    print("\nPlotting confusion matrix...")
    cnn_model.plot_confusion_matrix(X_test, y_test, class_names, 
                                    save_path='cnn_confusion_matrix.png')
    
    # Save model
    print("\n" + "="*70)
    print("SAVING MODEL")
    print("="*70)
    cnn_model.save_model('baseline_cnn_model.h5')
    

if __name__ == "__main__":
    main()