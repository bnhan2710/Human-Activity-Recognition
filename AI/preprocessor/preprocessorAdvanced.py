import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, QuantileTransformer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from scipy import signal, stats
from scipy.fft import fft, fftfreq
import os
import json
import warnings
warnings.filterwarnings('ignore')

class Preprocessor:
    
    def __init__(self):
        self.activities = {
            'WALKING': 1,
            'UPSTAIRS': 2, 
            'DOWNSTAIRS': 3,
            'SITTING': 4,
            'STANDING': 5,
            'RUNNING': 6
        }
        self.activity_names = list(self.activities.keys())
        self.n_classes = len(self.activities)
        
        # Raw sensor columns
        self.sensor_columns = [
            'ax_g', 'ay_g', 'az_g',           # Accelerometer
            'gx_dps', 'gy_dps', 'gz_dps',     # Gyroscope
            'amag_g',                          # Acceleration magnitude
            'pitch_kf', 'roll_kf'             # Orientation (Kalman filtered)
        ]
        self.n_raw_features = len(self.sensor_columns)
        
        # Target 45 features (optimal balance)
        self.n_target_features = 45
        
        # Windowing parameters
        self.window_size = 50  # 5 seconds at 20Hz
        self.overlap = 0.5   
        self.step_size = int(self.window_size * (1 - self.overlap))
        
        # Feature selection
        self.selected_feature_names = []
        self.feature_selector = None
        
    def extract_features_from_window(self, window_data):
        """
        Extract 72 features from a single window (100 samples x 9 sensors)
        Then use feature selection to keep best 45 features
        
        Features per sensor:
        - Time domain: mean, std, min, max, range, rms, variance, zero_crossing (8)
        - Frequency domain: spectral_energy, dominant_freq, spectral_entropy, fft_peak (4)
        Total: 12 features/sensor × 6 sensors = 72 features
        
        After selection: Keep 45 most important features
        """
        features = []
        
        # Process first 6 sensors (acc + gyro)
        for i in range(6):
            signal_data = window_data[:, i]
            
            # Time-domain features (8 features)
            mean_val = np.mean(signal_data)
            std_val = np.std(signal_data)
            min_val = np.min(signal_data)
            max_val = np.max(signal_data)
            range_val = max_val - min_val
            rms_val = np.sqrt(np.mean(signal_data**2))
            var_val = np.var(signal_data)
            
            # Zero crossing rate
            zero_crossings = np.sum(np.diff(np.sign(signal_data)) != 0)
            zcr = zero_crossings / len(signal_data)
            
            # Frequency-domain features (4 features)
            fft_vals = np.abs(fft(signal_data))
            freqs = fftfreq(len(signal_data), d=1/20)  # 20Hz sampling
            
            # Only positive frequencies
            positive_freqs = freqs[:len(freqs)//2]
            positive_fft = fft_vals[:len(fft_vals)//2]
            
            spectral_energy = np.sum(positive_fft**2)
            dominant_freq = positive_freqs[np.argmax(positive_fft)] if len(positive_fft) > 0 else 0
            
            # Spectral entropy
            psd = positive_fft**2
            psd_norm = psd / (np.sum(psd) + 1e-10)
            spectral_entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-10))
            
            fft_peak = np.max(positive_fft)
            
            # Append 12 features for this sensor
            features.extend([
                mean_val, std_val, min_val, max_val, range_val, 
                rms_val, var_val, zcr,
                spectral_energy, dominant_freq, spectral_entropy, fft_peak
            ])
        
        return np.array(features)
    
    def extract_all_features(self, X_windows):
        """Extract features from all windows"""
        print(f"\n🔧 Extracting 72 features from {len(X_windows)} windows...")
        
        X_features = []
        for i, window in enumerate(X_windows):
            if i % 1000 == 0:
                print(f"  Processing window {i}/{len(X_windows)}...", end='\r')
            
            features = self.extract_features_from_window(window[:, :6])  # Use only acc + gyro
            X_features.append(features)
        
        X_features = np.array(X_features)
        print(f"\n  ✅ Feature extraction complete. Shape: {X_features.shape}")
        
        return X_features
    
    def select_best_features(self, X_train_features, y_train, method='hybrid'):
        """
        Select best 45 features from 72 using hybrid approach:
        1. Random Forest feature importance (30 features)
        2. Mutual Information (15 features)
        Total: 45 unique features
        """
        print(f"\n🎯 Selecting top {self.n_target_features} features from 72...")
        
        # Method 1: Random Forest Feature Importance
        print("  Step 1/3: Computing Random Forest feature importance...")
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        rf.fit(X_train_features, y_train)
        rf_importances = rf.feature_importances_
        
        # Get top 30 features from RF
        rf_top_indices = np.argsort(rf_importances)[::-1][:30]
        
        # Method 2: Mutual Information
        print("  Step 2/3: Computing Mutual Information scores...")
        mi_selector = SelectKBest(mutual_info_classif, k=20)
        mi_selector.fit(X_train_features, y_train)
        mi_scores = mi_selector.scores_
        mi_top_indices = np.argsort(mi_scores)[::-1][:20]
        
        # Combine: RF top 30 + MI top 20 (remove duplicates)
        combined_indices = np.unique(np.concatenate([rf_top_indices, mi_top_indices]))
        
        # If we have more than target, keep top by combined score
        if len(combined_indices) > self.n_target_features:
            # Combined score: normalized RF importance + normalized MI score
            rf_norm = (rf_importances - rf_importances.min()) / (rf_importances.max() - rf_importances.min() + 1e-10)
            mi_norm = (mi_scores - mi_scores.min()) / (mi_scores.max() - mi_scores.min() + 1e-10)
            combined_scores = rf_norm + mi_norm
            
            selected_indices = np.argsort(combined_scores)[::-1][:self.n_target_features]
        else:
            # If less than target, add more from combined scores
            remaining = self.n_target_features - len(combined_indices)
            rf_norm = (rf_importances - rf_importances.min()) / (rf_importances.max() - rf_importances.min() + 1e-10)
            mi_norm = (mi_scores - mi_scores.min()) / (mi_scores.max() - mi_scores.min() + 1e-10)
            combined_scores = rf_norm + mi_norm
            
            all_indices = np.argsort(combined_scores)[::-1]
            selected_indices = []
            for idx in all_indices:
                if idx not in combined_indices or idx in combined_indices:
                    selected_indices.append(idx)
                if len(selected_indices) >= self.n_target_features:
                    break
            selected_indices = np.array(selected_indices)
        
        self.selected_feature_indices = sorted(selected_indices)
        
        # Generate feature names
        sensor_names = ['ax', 'ay', 'az', 'gx', 'gy', 'gz']
        feature_types = ['mean', 'std', 'min', 'max', 'range', 'rms', 'var', 'zcr',
                        'spec_energy', 'dom_freq', 'spec_entropy', 'fft_peak']
        
        self.selected_feature_names = []
        for idx in self.selected_feature_indices:
            sensor_idx = idx // 12
            feature_idx = idx % 12
            feature_name = f"{sensor_names[sensor_idx]}_{feature_types[feature_idx]}"
            self.selected_feature_names.append(feature_name)
        
        print(f"\n  ✅ Selected {len(self.selected_feature_indices)} features")
        print(f"\n  📊 Top 10 most important features:")
        for i, (idx, name) in enumerate(zip(self.selected_feature_indices[:10], 
                                            self.selected_feature_names[:10])):
            score = (rf_norm[idx] + mi_norm[idx]) / 2
            print(f"    {i+1:2d}. {name:25s} (score: {score:.4f})")
        
        return self.selected_feature_indices
    
    def create_sequences_from_features(self, X_features, n_timesteps=3):
        """
        Convert feature matrix to sequences for LSTM/GRU
        X_features: (n_windows, 45 features)
        Output: (n_windows, 3 timesteps, 45 features)
        
        Strategy: Split window into 3 equal segments and extract features from each
        """
        n_windows = X_features.shape[0]
        n_features = X_features.shape[1]
        
        # Reshape to (n_windows, n_timesteps, features_per_timestep)
        # Simple approach: Repeat features 3 times (will be replaced by actual segment features)
        X_sequences = np.zeros((n_windows, n_timesteps, n_features))
        
        # For simplicity, we'll use the same features for each timestep
        # In practice, you'd extract features from 3 segments of the original window
        for i in range(n_timesteps):
            X_sequences[:, i, :] = X_features
        
        return X_sequences
    
    def load_single_dataset(self, dataset_path, dataset_name):
        """Load single subject dataset"""
        print(f"\n📂 Loading {dataset_name} dataset from {dataset_path}")
        
        all_data = []
        activity_counts = {}
        
        for activity in self.activities.keys():
            activity_path = os.path.join(dataset_path, activity)
            if not os.path.exists(activity_path):
                print(f"  ⚠️ Activity folder not found: {activity_path}")
                continue
                
            activity_data = []
            csv_files = [f for f in os.listdir(activity_path) if f.endswith('.csv')]
            
            print(f"   {activity}: Found {len(csv_files)} files")
            
            for csv_file in csv_files:
                file_path = os.path.join(activity_path, csv_file)
                try:
                    df = pd.read_csv(file_path)
                    
                    missing_cols = [col for col in self.sensor_columns if col not in df.columns]
                    if missing_cols:
                        print(f"    ⚠️ Missing columns in {csv_file}: {missing_cols}")
                        continue
                    
                    df['activity'] = activity
                    df['dataset'] = dataset_name
                    df['subject'] = dataset_name
                    
                    activity_data.append(df)
                    
                except Exception as e:
                    print(f"    ❌ Error loading {csv_file}: {e}")
                    continue
            
            if activity_data:
                combined_activity = pd.concat(activity_data, ignore_index=True)
                all_data.append(combined_activity)
                activity_counts[activity] = len(combined_activity)
                print(f"    ✅ {activity}: {len(combined_activity)} samples")
        
        if all_data:
            dataset_df = pd.concat(all_data, ignore_index=True)
            print(f"  📊 Total {dataset_name} samples: {len(dataset_df)}")
            return dataset_df, activity_counts
        else:
            print(f"  ❌ No data loaded for {dataset_name}")
            return None, {}
    
    def load_combined_datasets(self, dataset_paths):
        """Load and combine multiple datasets"""
        print(f"🔄 Loading {len(dataset_paths)} datasets...")
        
        all_datasets = []
        all_counts = {}
        
        for dataset_name, dataset_path in dataset_paths.items():
            if dataset_path and os.path.exists(dataset_path):
                data, counts = self.load_single_dataset(dataset_path, dataset_name)
                if data is not None:
                    all_datasets.append(data)
                    all_counts[dataset_name] = counts
            else:
                print(f"⚠️ Skipping {dataset_name}: path not found or invalid")
        
        if not all_datasets:
            raise ValueError("❌ No datasets could be loaded!")
            
        combined_df = pd.concat(all_datasets, ignore_index=True)
        
        print(f"\n📊 Combined Dataset Summary:")
        print(f"  Total samples: {len(combined_df)}")
        print(f"  Number of subjects: {combined_df['dataset'].nunique()}")
        print(f"  Subjects: {', '.join(combined_df['dataset'].unique())}")
        
        return combined_df
    
    def clean_data(self, df):
        """Clean data: remove NaN and outliers"""
        initial_size = len(df)
        print(f"\n🧹 Cleaning data (initial size: {initial_size})...")
        
        df_clean = df.dropna(subset=self.sensor_columns)
        nan_removed = initial_size - len(df_clean)
        if nan_removed > 0:
            print(f"  Removed {nan_removed} rows with NaN values.")
        
        for col in self.sensor_columns:
            Q1 = df_clean[col].quantile(0.05)
            Q3 = df_clean[col].quantile(0.95)
            IQR = Q3 - Q1
            lower_bound = Q1 - 5.0 * IQR
            upper_bound = Q3 + 5.0 * IQR
            
            before_count = len(df_clean)
            df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]
            removed = before_count - len(df_clean)
            if removed > 0:
                print(f"  Removed {removed} outliers from {col}")
        
        final_size = len(df_clean)
        print(f"  ✨ Cleaning complete. Final size: {final_size} ({(final_size/initial_size)*100:.1f}% retained)")
        return df_clean
    
    def balance_dataset(self, df, method='smart_balance'):
        """Smart balance dataset"""
        print(f"\n⚖️ Smart balancing dataset...")
        
        activity_counts = df['activity'].value_counts()
        print("  Before balancing:")
        for activity, count in activity_counts.items():
            percentage = (count / len(df)) * 100
            print(f"    {activity}: {count} ({percentage:.2f}%)")
        
        median_count = int(activity_counts.median())
        max_allowed = int(median_count * 2.5)
        
        print(f"\n  🎯 Target range: {median_count} to {max_allowed} samples per class")
        
        balanced_dfs = []
        for activity in df['activity'].unique():
            activity_df = df[df['activity'] == activity]
            current_count = len(activity_df)
            
            if current_count > max_allowed:
                print(f"    {activity}: {current_count} → {max_allowed} (downsampling)")
                activity_df = activity_df.sample(n=max_allowed, random_state=42)
            elif current_count < median_count * 0.5:
                target = int(median_count * 0.8)
                print(f"    {activity}: {current_count} → {target} (upsampling)")
                additional = target - current_count
                extra_df = activity_df.sample(n=additional, replace=True, random_state=42)
                activity_df = pd.concat([activity_df, extra_df], ignore_index=True)
            else:
                print(f"    {activity}: {current_count} (kept as is)")
            
            balanced_dfs.append(activity_df)
        
        balanced_df = pd.concat(balanced_dfs, ignore_index=True)
        print(f"  ✅ Total samples after balancing: {len(balanced_df)}")
        
        return balanced_df
    
    def create_sliding_windows(self, df):
        """Create sliding windows from continuous data"""
        print(f"\n🪟 Creating sliding windows...")
        print(f"  Window size: {self.window_size} samples ({self.window_size/20:.1f} seconds)")
        print(f"  Overlap: {self.overlap*100:.0f}% ({self.window_size - self.step_size} samples)")
        
        X_windows, y_windows, subject_windows = [], [], []
        
        for subject in df['dataset'].unique():
            for activity in df['activity'].unique():
                subset = df[(df['dataset'] == subject) & (df['activity'] == activity)]
                
                if len(subset) < self.window_size:
                    continue
                
                if 'time_ms' in subset.columns:
                    subset = subset.sort_values('time_ms')
                
                sensor_data = subset[self.sensor_columns].values
                activity_label = self.activities[activity]
                
                for i in range(0, len(sensor_data) - self.window_size + 1, self.step_size):
                    window = sensor_data[i:i + self.window_size]
                    X_windows.append(window)
                    y_windows.append(activity_label - 1)
                    subject_windows.append(subject)
        
        X_windows = np.array(X_windows)
        y_windows = np.array(y_windows)
        subject_windows = np.array(subject_windows)
        
        print(f"  ✅ Total windows created: {len(X_windows)}")
        print(f"  📐 Window shape: {X_windows.shape}")
        
        return X_windows, y_windows, subject_windows

    def prepare_data(self, dataset_paths, test_subject_idx=3, val_subject_idx=1):
        """Main preprocessing pipeline with feature engineering"""
        
        # 1-6: Same as before (load, clean, balance, window)
        df = self.load_combined_datasets(dataset_paths)
        df_clean = self.clean_data(df)
        
        print("\n📏 Applying QuantileTransformer...")
        qt = QuantileTransformer(output_distribution='normal', n_quantiles=1000, random_state=42)
        qt.fit(df_clean[self.sensor_columns])
        df_clean[self.sensor_columns] = qt.transform(df_clean[self.sensor_columns])
        
        df_balanced = self.balance_dataset(df_clean)
        X_windows, y_windows, subject_windows = self.create_sliding_windows(df_balanced)
        
        # 7. Subject-wise split
        unique_subjects = sorted(list(np.unique(subject_windows)))
        test_subject = unique_subjects[test_subject_idx]
        val_subject = unique_subjects[val_subject_idx]
        train_subjects = [s for s in unique_subjects if s not in [test_subject, val_subject]]
        
        train_mask = np.isin(subject_windows, train_subjects)
        val_mask = np.isin(subject_windows, [val_subject])
        test_mask = np.isin(subject_windows, [test_subject])
        
        X_train_windows = X_windows[train_mask]
        y_train = y_windows[train_mask]
        X_val_windows = X_windows[val_mask]
        y_val = y_windows[val_mask]
        X_test_windows = X_windows[test_mask]
        y_test = y_windows[test_mask]
        
        # 8. Extract 72 features
        X_train_features = self.extract_all_features(X_train_windows)
        X_val_features = self.extract_all_features(X_val_windows)
        X_test_features = self.extract_all_features(X_test_windows)
        
        # 9. Feature selection (on train only)
        self.select_best_features(X_train_features, y_train)
        
        # Apply selection to all sets
        X_train_selected = X_train_features[:, self.selected_feature_indices]
        X_val_selected = X_val_features[:, self.selected_feature_indices]
        X_test_selected = X_test_features[:, self.selected_feature_indices]
        
        print(f"\n  📊 Feature selection applied:")
        print(f"    Train: {X_train_features.shape} → {X_train_selected.shape}")
        print(f"    Val:   {X_val_features.shape} → {X_val_selected.shape}")
        print(f"    Test:  {X_test_features.shape} → {X_test_selected.shape}")
        
        # 10. Normalize selected features
        print("\n📏 Normalizing selected features with StandardScaler...")
        scaler = StandardScaler()
        scaler.fit(X_train_selected)
        
        X_train_scaled = scaler.transform(X_train_selected)
        X_val_scaled = scaler.transform(X_val_selected)
        X_test_scaled = scaler.transform(X_test_selected)
        
        # 11. Create sequences for GRU (3 timesteps)
        print("\n🔄 Creating sequences for GRU (3 timesteps)...")
        X_train = self.create_sequences_from_features(X_train_scaled, n_timesteps=3)
        X_val = self.create_sequences_from_features(X_val_scaled, n_timesteps=3)
        X_test = self.create_sequences_from_features(X_test_scaled, n_timesteps=3)
        
        print(f"\n✅ Final shapes:")
        print(f"  Train: {X_train.shape} (windows, timesteps, features)")
        print(f"  Val:   {X_val.shape}")
        print(f"  Test:  {X_test.shape}")

        print(f" Train subjects: {train_subjects}")
        print(f" Val subject: {val_subject}")
        print(f" Test subject: {test_subject}")
        
        # Save preprocessing info
        preprocessing_info = {
            'scaler_mean': scaler.mean_.tolist(),
            'scaler_scale': scaler.scale_.tolist(),
            'selected_feature_indices': [int(idx) for idx in self.selected_feature_indices],  # Convert numpy int64 to Python int
            'selected_feature_names': self.selected_feature_names,
            'n_features': int(self.n_target_features),
            'n_timesteps': 3,
            'window_size': int(self.window_size),
            'overlap': float(self.overlap),
            'n_classes': int(self.n_classes),
            'activities': {int(v-1): k for k, v in self.activities.items()},
            'test_subject': test_subject,
            'val_subject': val_subject,
            'train_subjects': train_subjects
        }
        
        with open('preprocessing_info_features.json', 'w') as f:
            json.dump(preprocessing_info, f, indent=4)
        print("\n💾 Preprocessing info saved to preprocessing_info_features.json")
        
        return X_train, X_val, X_test, y_train, y_val, y_test, scaler