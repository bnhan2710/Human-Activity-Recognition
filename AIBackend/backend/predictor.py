"""
Activity Predictor Module
Handles model loading and prediction logic
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler, QuantileTransformer
import logging
from typing import Tuple, Dict, List
import os
import pickle
import json

logger = logging.getLogger(__name__)


class ActivityPredictor:
    """
    Handles activity prediction from preprocessed sensor data
    """
    
    def __init__(self, model_path: str, artifacts_path: str = None, scaler_path: str = None):
        """
        Initialize predictor with trained model and preprocessing artifacts
        
        Args:
            model_path: Path to the trained .h5 model file
            artifacts_path: Path to model_artifacts directory (RECOMMENDED - contains scalers + metadata)
            scaler_path: Legacy path to scalers directory (deprecated, use artifacts_path instead)
        """
        self.model_path = model_path
        self.artifacts_path = artifacts_path
        self.scaler_path = scaler_path if not artifacts_path else artifacts_path
        
        # Activity mapping (same as training)
        self.activities = {
            'WALKING': 1, 'UPSTAIRS': 2, 'DOWNSTAIRS': 3,
            'SITTING': 4, 'STANDING': 5, 'RUNNING': 6
        }
        self.activity_names = list(self.activities.keys())
        self.idx_to_activity = {i: name for i, name in enumerate(self.activity_names)}
        self.n_classes = len(self.activities)
        
        # Feature configuration (from training pipeline)
        self.sensor_columns = [
            'ax_g', 'ay_g', 'az_g', 'gx_dps', 'gy_dps', 'gz_dps',     
            'amag_g', 'pitch_kf', 'roll_kf'
        ]
        self.derivative_columns = ['d_pitch_kf', 'd_roll_kf']
        self.all_feature_columns = self.sensor_columns + self.derivative_columns
        self.n_features_raw = len(self.sensor_columns)
        self.n_features = len(self.all_feature_columns)
        
        # Window configuration
        self.window_size = 40  # 2s at 20Hz
        self.overlap = 0.5
        self.step_size = int(self.window_size * (1 - self.overlap))
        
        # Load model
        self.model = self._load_model()
        
        # Load preprocessing artifacts (scalers + metadata)
        if artifacts_path:
            self._load_artifacts(artifacts_path)
        elif scaler_path:
            logger.warning("⚠️  Using legacy scaler_path. Consider using artifacts_path for better validation.")
            self._load_scalers(scaler_path)
        else:
            # Fallback to on-the-fly fitting (NOT RECOMMENDED!)
            logger.error("="*80)
            logger.error("❌ NO ARTIFACTS PROVIDED - PREDICTIONS WILL BE INACCURATE!")
            logger.error("❌ Run 'python save_model_artifacts.py' in AI/ directory")
            logger.error("="*80)
            self.qt = QuantileTransformer(output_distribution='normal', n_quantiles=1000, random_state=42)
            self.scaler = StandardScaler()
            self.scalers_fitted = False
        
        logger.info(f"✅ ActivityPredictor initialized with model: {os.path.basename(model_path)}")
    
    def _load_model(self) -> keras.Model:
        """Load the trained Keras model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        try:
            # Custom objects for weighted loss (if needed)
            custom_objects = {}
            
            model = keras.models.load_model(self.model_path, custom_objects=custom_objects, compile=False)
            logger.info(f" Model loaded from {self.model_path}")
            logger.info(f"   Input shape: {model.input_shape}")
            logger.info(f"   Output shape: {model.output_shape}")
            
            return model
        
        except Exception as e:
            logger.error(f" Failed to load model: {e}")
            raise
    
    def _load_artifacts(self, artifacts_path: str):
        """
        Load preprocessing artifacts (scalers + metadata) from training
        This ensures inference preprocessing matches training exactly!
        
        Args:
            artifacts_path: Directory containing model artifacts
        """
        try:
            logger.info(f"📦 Loading model artifacts from: {artifacts_path}")
            
            # Try to find quantile_transformer file (with or without suffix)
            qt_candidates = [
                'quantile_transformer.pkl',
                'quantile_transformer_BINH_PHONG.pkl',
            ]
            
            qt_path = None
            for candidate in qt_candidates:
                candidate_path = os.path.join(artifacts_path, candidate)
                if os.path.exists(candidate_path):
                    qt_path = candidate_path
                    break
            
            if not qt_path:
                raise FileNotFoundError(f"QuantileTransformer not found in: {artifacts_path}")
            
            with open(qt_path, 'rb') as f:
                self.qt = pickle.load(f)
            logger.info(f"   ✅ Loaded QuantileTransformer from: {os.path.basename(qt_path)}")
            
            # Try to find standard_scaler file (with or without suffix)
            scaler_candidates = [
                'standard_scaler.pkl',
                'standard_scaler_BINH_PHONG.pkl',
            ]
            
            scaler_path = None
            for candidate in scaler_candidates:
                candidate_path = os.path.join(artifacts_path, candidate)
                if os.path.exists(candidate_path):
                    scaler_path = candidate_path
                    break
            
            if not scaler_path:
                raise FileNotFoundError(f"StandardScaler not found in: {artifacts_path}")
            
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"   ✅ Loaded StandardScaler from: {os.path.basename(scaler_path)}")
            
            # Load and validate metadata (optional - for validation only)
            metadata_candidates = [
                'preprocessing_metadata.json',
                'model_config_BINH_PHONG.json',
            ]
            
            metadata_path = None
            for candidate in metadata_candidates:
                candidate_path = os.path.join(artifacts_path, candidate)
                if os.path.exists(candidate_path):
                    metadata_path = candidate_path
                    break
            
            if metadata_path:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                logger.info(f"   📄 Loaded metadata from: {os.path.basename(metadata_path)}")
                
                # Validate configuration matches (if metadata has these fields)
                if 'window_size' in metadata:
                    train_window_size = metadata['window_size']
                    if train_window_size != self.window_size:
                        logger.warning(f"⚠️  Window size mismatch! Training: {train_window_size}, Current: {self.window_size}")
                
                if 'n_features' in metadata:
                    train_n_features = metadata['n_features']
                    if train_n_features != self.n_features:
                        logger.warning(f"⚠️  Feature count mismatch! Training: {train_n_features}, Current: {self.n_features}")
                
                # Log training info
                if 'train_subjects' in metadata:
                    logger.info(f"   📊 Training info:")
                    logger.info(f"      - Train subjects: {metadata.get('train_subjects', 'N/A')}")
                    logger.info(f"      - Test subjects: {metadata.get('test_subjects', 'N/A')}")
                    logger.info(f"      - Val subject: {metadata.get('val_subject', 'N/A')}")
            else:
                logger.info(f"   ℹ️  No metadata file found (optional)")
            
            self.scalers_fitted = True
            logger.info("✅ All artifacts loaded successfully - preprocessing will match training!")
            
        except Exception as e:
            logger.error(f"❌ Failed to load artifacts: {e}")
            logger.warning("⚠️  Falling back to on-the-fly fitting (NOT RECOMMENDED!)")
            self.qt = QuantileTransformer(output_distribution='normal', n_quantiles=1000, random_state=42)
            self.scaler = StandardScaler()
            self.scalers_fitted = False
    
    def _load_scalers(self, scaler_path: str):
        """
        Load pre-fitted scalers from training
        
        Args:
            scaler_path: Directory containing scaler pickle files
        """
        try:
            qt_path = os.path.join(scaler_path, 'quantile_transformer.pkl')
            scaler_path_full = os.path.join(scaler_path, 'standard_scaler.pkl')
            
            if not os.path.exists(qt_path):
                raise FileNotFoundError(f"QuantileTransformer not found: {qt_path}")
            if not os.path.exists(scaler_path_full):
                raise FileNotFoundError(f"StandardScaler not found: {scaler_path_full}")
            
            with open(qt_path, 'rb') as f:
                self.qt = pickle.load(f)
            
            with open(scaler_path_full, 'rb') as f:
                self.scaler = pickle.load(f)
            
            self.scalers_fitted = True
            logger.info("✅ Loaded pre-fitted scalers from training")
            logger.info(f"   QuantileTransformer: {qt_path}")
            logger.info(f"   StandardScaler: {scaler_path_full}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load scalers: {e}")
            logger.warning("⚠️  Falling back to on-the-fly fitting (NOT RECOMMENDED!)")
            self.qt = QuantileTransformer(output_distribution='normal', n_quantiles=1000, random_state=42)
            self.scaler = StandardScaler()
            self.scalers_fitted = False
    
    def _compute_derivatives(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute derivative features (d_pitch_kf, d_roll_kf)
        
        Args:
            df: DataFrame with sensor data
            
        Returns:
            DataFrame with derivative features added
        """
        df = df.copy()
        df['d_pitch_kf'] = df['pitch_kf'].diff().fillna(0)
        df['d_roll_kf'] = df['roll_kf'].diff().fillna(0)
        return df
    
    def _preprocess_window(self, window: np.ndarray) -> np.ndarray:
        """
        Preprocess a single window following the training pipeline:
        1. Separate raw features (9) and derivatives (2)
        2. Apply QuantileTransformer to raw features
        3. Combine back to 11 features
        4. Apply StandardScaler to all features
        
        Args:
            window: Window of shape (window_size, n_features)
            
        Returns:
            Preprocessed window of same shape
        """
        # Separate raw and derivative features
        window_raw_9 = window[:, :self.n_features_raw]  # First 9 features
        window_deriv_2 = window[:, self.n_features_raw:]  # Last 2 features
        
        # Apply QuantileTransformer to raw features
        window_raw_9_flat = window_raw_9.reshape(-1, self.n_features_raw)
        
        if not self.scalers_fitted:
            # Fit on first window (not ideal, but works for inference)
            self.qt.fit(window_raw_9_flat)
            logger.warning("⚠️ ⚠️ ⚠️ Fitting QuantileTransformer on single window - PREDICTIONS WILL BE INACCURATE!")
            logger.warning("⚠️ Run 'cd ../AI && python save_scalers.py' to fix this!")
        
        window_raw_9_transformed = self.qt.transform(window_raw_9_flat).reshape(window_raw_9.shape)
        
        # Combine raw and derivatives
        window_combined = np.concatenate([window_raw_9_transformed, window_deriv_2], axis=1)
        
        # Apply StandardScaler
        window_combined_flat = window_combined.reshape(-1, self.n_features)
        
        if not self.scalers_fitted:
            # Fit on first window
            self.scaler.fit(window_combined_flat)
            self.scalers_fitted = True
            logger.warning("⚠️ ⚠️ ⚠️ Fitting StandardScaler on single window - PREDICTIONS WILL BE INACCURATE!")
            logger.warning("⚠️ Run 'cd ../AI && python save_scalers.py' to fix this!")
        
        window_normalized = self.scaler.transform(window_combined_flat).reshape(window_combined.shape)
        
        return window_normalized
    
    def predict_window(self, window: np.ndarray) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict activity from a preprocessed window
        
        Args:
            window: Window of sensor data, shape (window_size, n_features)
            
        Returns:
            Tuple of (activity_name, confidence, probabilities_dict)
        """
        if window.shape[0] != self.window_size:
            raise ValueError(f"Window size mismatch. Expected {self.window_size}, got {window.shape[0]}")
        
        if window.shape[1] != self.n_features:
            raise ValueError(f"Feature count mismatch. Expected {self.n_features}, got {window.shape[1]}")
        
        # Preprocess window
        window_preprocessed = self._preprocess_window(window)
        
        # Add batch dimension
        window_batch = np.expand_dims(window_preprocessed, axis=0)
        
        # Predict
        predictions = self.model.predict(window_batch, verbose=0)
        predicted_class = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class])
        
        # Get activity name
        activity = self.idx_to_activity[predicted_class]
        
        # Create probabilities dict
        probabilities = {
            self.idx_to_activity[i]: float(predictions[0][i])
            for i in range(self.n_classes)
        }
        
        return activity, confidence, probabilities
    
    def predict_from_dataframe(self, df: pd.DataFrame, use_sliding_window: bool = True) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict activity from a DataFrame of sensor readings
        
        Args:
            df: DataFrame with sensor columns
            use_sliding_window: If True, use the last window_size samples. If False, use all data.
            
        Returns:
            Tuple of (activity_name, confidence, probabilities_dict)
        """
        # Validate columns
        missing_cols = [col for col in self.sensor_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Sort by timestamp if available
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Compute derivatives
        df = self._compute_derivatives(df)
        
        # Extract features
        features = df[self.all_feature_columns].values
        
        if len(features) < self.window_size:
            raise ValueError(f"Not enough data. Need at least {self.window_size} samples, got {len(features)}")
        
        if use_sliding_window:
            # Use the last window
            window = features[-self.window_size:]
        else:
            # Use the first window (or could do majority voting over multiple windows)
            window = features[:self.window_size]
        
        return self.predict_window(window)
    
    def predict_multiple_windows(self, df: pd.DataFrame) -> List[Dict]:
        """
        Predict activity for multiple sliding windows in the DataFrame
        Useful for analyzing longer recordings

        Args:
            df: DataFrame with sensor columns
            
        Returns:
            List of prediction dictionaries
        """
        # Validate columns
        missing_cols = [col for col in self.sensor_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Sort by timestamp if available
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Compute derivatives
        df = self._compute_derivatives(df)
        
        # Extract features
        features = df[self.all_feature_columns].values
        
        if len(features) < self.window_size:
            raise ValueError(f"Not enough data. Need at least {self.window_size} samples, got {len(features)}")
        
        # Create sliding windows
        predictions = []
        for i in range(0, len(features) - self.window_size + 1, self.step_size):
            window = features[i:i + self.window_size]
            activity, confidence, probabilities = self.predict_window(window)
            
            predictions.append({
                'window_start': i,
                'window_end': i + self.window_size,
                'activity': activity,
                'confidence': confidence,
                'probabilities': probabilities
            })
        
        return predictions
    
    def get_majority_prediction(self, df: pd.DataFrame) -> Tuple[str, float, Dict[str, float]]:
        """
        Get majority vote prediction from multiple windows
        More robust for longer recordings
        
        Args:
            df: DataFrame with sensor columns
            
        Returns:
            Tuple of (activity_name, average_confidence, average_probabilities)
        """
        predictions = self.predict_multiple_windows(df)
        
        if not predictions:
            raise ValueError("No predictions generated")
        
        # Count activities
        activity_counts = {}
        activity_confidences = {}
        
        for pred in predictions:
            activity = pred['activity']
            confidence = pred['confidence']
            
            if activity not in activity_counts:
                activity_counts[activity] = 0
                activity_confidences[activity] = []
            
            activity_counts[activity] += 1
            activity_confidences[activity].append(confidence)
        
        # Get majority activity
        majority_activity = max(activity_counts, key=activity_counts.get)
        avg_confidence = float(np.mean(activity_confidences[majority_activity]))
        
        # Average probabilities
        avg_probabilities = {}
        for activity in self.activity_names:
            probs = [p['probabilities'][activity] for p in predictions]
            avg_probabilities[activity] = float(np.mean(probs))
        
        return majority_activity, avg_confidence, avg_probabilities
