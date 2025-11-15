"""
Data Buffer Module
Manages circular buffer for real-time sensor data streaming
"""

import numpy as np
import pandas as pd
from collections import deque
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataBuffer:
    """
    Circular buffer for sensor data with sliding window support
    """
    
    def __init__(self, window_size: int = 40, overlap: float = 0.5):
        """
        Initialize data buffer
        
        Args:
            window_size: Number of samples in a prediction window
            overlap: Overlap ratio for sliding windows (0.0 to 1.0)
        """
        self.window_size = window_size
        self.overlap = overlap
        self.step_size = int(window_size * (1 - overlap))
        
        # Required sensor columns
        self.sensor_columns = [
            'ax_g', 'ay_g', 'az_g', 'gx_dps', 'gy_dps', 'gz_dps',     
            'amag_g', 'pitch_kf', 'roll_kf'
        ]
        
        # Circular buffer using deque
        self.buffer = deque(maxlen=window_size * 2)  # Keep 2x window size for sliding
        
        logger.info(f"✅ DataBuffer initialized: window_size={window_size}, overlap={overlap}")
    
    def add_sample(self, sample: Dict):
        """
        Add a single sensor sample to the buffer
        
        Args:
            sample: Dictionary with sensor readings
        """
        # Validate sample has required columns
        missing = [col for col in self.sensor_columns if col not in sample]
        if missing:
            logger.warning(f"Sample missing columns: {missing}")
            return
        
        # Add timestamp if not present
        if 'timestamp' not in sample:
            sample['timestamp'] = int(datetime.now().timestamp() * 1000)
        
        # Add to buffer
        self.buffer.append(sample)
        
        logger.debug(f"Added sample to buffer. Buffer size: {len(self.buffer)}/{self.window_size}")
    
    def add_batch(self, samples: List[Dict]):
        """
        Add multiple samples to the buffer
        
        Args:
            samples: List of sample dictionaries
        """
        for sample in samples:
            self.add_sample(sample)
    
    def can_predict(self) -> bool:
        """
        Check if buffer has enough data for prediction
        
        Returns:
            True if buffer size >= window_size
        """
        return len(self.buffer) >= self.window_size
    
    def get_window(self) -> np.ndarray:
        """
        Get the latest window of data for prediction
        
        Returns:
            Numpy array of shape (window_size, n_features)
        """
        if not self.can_predict():
            raise ValueError(f"Not enough data in buffer. Need {self.window_size}, have {len(self.buffer)}")
        
        # Get last window_size samples
        window_data = list(self.buffer)[-self.window_size:]
        
        # Convert to DataFrame
        df = pd.DataFrame(window_data)
        
        # Sort by timestamp
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Compute derivatives
        df['d_pitch_kf'] = df['pitch_kf'].diff().fillna(0)
        df['d_roll_kf'] = df['roll_kf'].diff().fillna(0)
        
        # Extract features in correct order
        feature_columns = self.sensor_columns + ['d_pitch_kf', 'd_roll_kf']
        window_array = df[feature_columns].values
        
        return window_array
    
    def get_buffer_size(self) -> int:
        """
        Get current buffer size
        
        Returns:
            Number of samples in buffer
        """
        return len(self.buffer)
    
    def get_buffer_as_dataframe(self) -> pd.DataFrame:
        """
        Get entire buffer as DataFrame
        
        Returns:
            DataFrame with all buffer data
        """
        if len(self.buffer) == 0:
            return pd.DataFrame()
        
        return pd.DataFrame(list(self.buffer))
    
    def clear(self):
        """Clear all data from buffer"""
        self.buffer.clear()
        logger.info("🗑️ Buffer cleared")
    
    def get_statistics(self) -> Dict:
        """
        Get buffer statistics
        
        Returns:
            Dictionary with buffer statistics
        """
        if len(self.buffer) == 0:
            return {
                'size': 0,
                'can_predict': False,
                'fill_percentage': 0.0
            }
        
        df = self.get_buffer_as_dataframe()
        
        stats = {
            'size': len(self.buffer),
            'can_predict': self.can_predict(),
            'fill_percentage': (len(self.buffer) / self.window_size) * 100,
            'time_span_ms': None,
            'sample_rate_hz': None
        }
        
        # Calculate time span and sample rate if timestamps available
        if 'timestamp' in df.columns and len(df) > 1:
            timestamps = df['timestamp'].values
            time_span_ms = timestamps[-1] - timestamps[0]
            stats['time_span_ms'] = int(time_span_ms)
            
            if time_span_ms > 0:
                sample_rate = (len(df) - 1) / (time_span_ms / 1000.0)
                stats['sample_rate_hz'] = round(sample_rate, 2)
        
        return stats
    
    def __len__(self) -> int:
        """Get buffer size"""
        return len(self.buffer)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"DataBuffer(size={len(self.buffer)}/{self.window_size}, can_predict={self.can_predict()})"


class RollingBuffer(DataBuffer):
    """
    Enhanced buffer with rolling statistics and outlier detection
    """
    
    def __init__(self, window_size: int = 40, overlap: float = 0.5, 
                 enable_outlier_detection: bool = True):
        """
        Initialize rolling buffer with advanced features
        
        Args:
            window_size: Number of samples in a prediction window
            overlap: Overlap ratio for sliding windows
            enable_outlier_detection: Enable automatic outlier detection
        """
        super().__init__(window_size, overlap)
        self.enable_outlier_detection = enable_outlier_detection
        
        # Rolling statistics
        self.rolling_stats = {col: {'mean': 0, 'std': 0, 'min': 0, 'max': 0} 
                             for col in self.sensor_columns}
    
    def _update_rolling_stats(self):
        """Update rolling statistics"""
        if len(self.buffer) < 2:
            return
        
        df = self.get_buffer_as_dataframe()
        
        for col in self.sensor_columns:
            if col in df.columns:
                self.rolling_stats[col] = {
                    'mean': float(df[col].mean()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max())
                }
    
    def _is_outlier(self, sample: Dict) -> bool:
        """
        Check if sample is an outlier based on rolling statistics
        
        Args:
            sample: Sample dictionary
            
        Returns:
            True if sample is likely an outlier
        """
        if len(self.buffer) < 10:  # Need some data first
            return False
        
        # Check each sensor column
        outlier_count = 0
        for col in self.sensor_columns:
            if col not in sample:
                continue
            
            value = sample[col]
            stats = self.rolling_stats[col]
            
            # Z-score based outlier detection
            if stats['std'] > 0:
                z_score = abs((value - stats['mean']) / stats['std'])
                if z_score > 4.0:  # More than 4 standard deviations
                    outlier_count += 1
        
        # If more than 30% of features are outliers, flag the sample
        outlier_ratio = outlier_count / len(self.sensor_columns)
        return outlier_ratio > 0.3
    
    def add_sample(self, sample: Dict):
        """
        Add sample with outlier detection
        
        Args:
            sample: Sample dictionary
        """
        # Check for outliers if enabled
        if self.enable_outlier_detection and self._is_outlier(sample):
            logger.warning(f"⚠️ Outlier detected, skipping sample")
            return
        
        # Add to buffer
        super().add_sample(sample)
        
        # Update rolling statistics
        self._update_rolling_stats()
    
    def get_rolling_stats(self) -> Dict:
        """
        Get current rolling statistics
        
        Returns:
            Dictionary with rolling statistics for each sensor
        """
        return self.rolling_stats.copy()
