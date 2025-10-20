import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
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
        

        self.sensor_columns = [
            'ax_g', 'ay_g', 'az_g',           # Accelerometer
            'gx_dps', 'gy_dps', 'gz_dps',     # Gyroscope
            'amag_g',                          # Acceleration magnitude
            'pitch_kf', 'roll_kf'             # Orientation (Kalman filtered)
        ]
        self.n_features = len(self.sensor_columns)
        

        self.window_size = 20 
        self.overlap = 0.5   
        self.step_size = int(self.window_size * (1 - self.overlap))
        
    def load_single_dataset(self, dataset_path, dataset_name):

        print(f"\n Loading {dataset_name} dataset from {dataset_path}")
        
        all_data = []
        activity_counts = {}
        
        for activity in self.activities.keys():
            activity_path = os.path.join(dataset_path, activity)
            if not os.path.exists(activity_path):
                print(f"  Activity folder not found: {activity_path}")
                continue
                
            activity_data = []
            csv_files = [f for f in os.listdir(activity_path) if f.endswith('.csv')]
            
            print(f"   {activity}: Found {len(csv_files)} files")
            
            for csv_file in csv_files:
                file_path = os.path.join(activity_path, csv_file)
                try:
                    df = pd.read_csv(file_path)
                    
                    # Check if all required columns exist
                    missing_cols = [col for col in self.sensor_columns if col not in df.columns]
                    if missing_cols:
                        print(f"    Missing columns in {csv_file}: {missing_cols}")
                        continue
                    
                    df['activity'] = activity
                    df['dataset'] = dataset_name
                    df['subject'] = dataset_name
                    
                    activity_data.append(df)
                    
                except Exception as e:
                    print(f"    Error loading {csv_file}: {e}")
                    continue
            
            if activity_data:
                combined_activity = pd.concat(activity_data, ignore_index=True)
                all_data.append(combined_activity)
                activity_counts[activity] = len(combined_activity)
                print(f"    {activity}: {len(combined_activity)} samples")
        
        if all_data:
            dataset_df = pd.concat(all_data, ignore_index=True)
            print(f"  Total {dataset_name} samples: {len(dataset_df)}")
            return dataset_df, activity_counts
        else:
            print(f"  No data loaded for {dataset_name}")
            return None, {}
    
    def load_combined_datasets(self, dataset_paths):
        print(f" Loading {len(dataset_paths)} datasets...")
        
        all_datasets = []
        all_counts = {}
        
        for dataset_name, dataset_path in dataset_paths.items():
            if dataset_path and os.path.exists(dataset_path):
                data, counts = self.load_single_dataset(dataset_path, dataset_name)
                if data is not None:
                    all_datasets.append(data)
                    all_counts[dataset_name] = counts
            else:
                print(f" Skipping {dataset_name}: path not found or invalid")
        
        if not all_datasets:
            raise ValueError(" No datasets could be loaded!")
            
        combined_df = pd.concat(all_datasets, ignore_index=True)
        
        print(f"\n Combined Dataset Summary:")
        print(f"  Total samples: {len(combined_df)}")
        print(f"  Number of subjects: {combined_df['dataset'].nunique()}")
        print(f"  Subjects: {', '.join(combined_df['dataset'].unique())}")
        print(f"  Activities: {', '.join(combined_df['activity'].unique())}")
        
        print(f"\n Activity Distribution by Subject:")
        for dataset_name in combined_df['dataset'].unique():
            dataset_subset = combined_df[combined_df['dataset'] == dataset_name]
            print(f"\n  {dataset_name}:")
            activity_dist = dataset_subset['activity'].value_counts().sort_index()
            for activity, count in activity_dist.items():
                print(f"    {activity}: {count} samples")
        
        print(f"\n Total Activity Distribution:")
        activity_dist = combined_df['activity'].value_counts().sort_index()
        for activity, count in activity_dist.items():
            percentage = (count / len(combined_df)) * 100
            print(f"  {activity}: {count} samples ({percentage:.2f}%)")
            
        return combined_df
    
    def clean_data(self, df):
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
            lower_bound = Q1 - 3.0 * IQR
            upper_bound = Q3 + 3.0 * IQR
            
            before_count = len(df_clean)
            df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]
            removed = before_count - len(df_clean)
            if removed > 0:
                print(f"  Removed {removed} outliers from {col}")
        
        final_size = len(df_clean)
        print(f"  ✨ Cleaning complete. Final size: {final_size} ({(final_size/initial_size)*100:.1f}% retained)")
        return df_clean
    
    def balance_dataset(self, df, method='smart_balance'):

        print(f"\n Smart balancing dataset...")
        
        activity_counts = df['activity'].value_counts()
        print("  Before balancing:")
        for activity, count in activity_counts.items():
            percentage = (count / len(df)) * 100
            print(f"    {activity}: {count} ({percentage:.2f}%)")
        
        # Calculate target: median count (not min!)
        median_count = int(activity_counts.median())
        max_allowed = int(median_count * 2.5)  # Allow some imbalance
        
        print(f"\n   Target range: {median_count} to {max_allowed} samples per class")
        
        balanced_dfs = []
        for activity in df['activity'].unique():
            activity_df = df[df['activity'] == activity]
            current_count = len(activity_df)
            
            if current_count > max_allowed:
                # Downsample only extreme cases
                print(f"    {activity}: {current_count} → {max_allowed} (downsampling)")
                activity_df = activity_df.sample(n=max_allowed, random_state=42)
            elif current_count < median_count * 0.5:
                # Upsample only very small classes
                target = int(median_count * 0.8)
                print(f"    {activity}: {current_count} → {target} (upsampling)")
                additional = target - current_count
                extra_df = activity_df.sample(n=additional, replace=True, random_state=42)
                activity_df = pd.concat([activity_df, extra_df], ignore_index=True)
            else:
                print(f"    {activity}: {current_count} (kept as is)")
            
            balanced_dfs.append(activity_df)
        
        balanced_df = pd.concat(balanced_dfs, ignore_index=True)
        
        print("\n  After smart balancing:")
        for activity, count in balanced_df['activity'].value_counts().items():
            percentage = (count / len(balanced_df)) * 100
            print(f"    {activity}: {count} ({percentage:.2f}%)")
        
        print(f"  Total samples: {len(balanced_df)}")
        return balanced_df
    
    def create_sliding_windows(self, df):
        """Create sliding windows from continuous data"""
        print(f"\n Creating sliding windows...")
        print(f"  Window size: {self.window_size} samples ({self.window_size/20:.1f} seconds)")
        print(f"  Overlap: {self.overlap*100:.0f}% ({self.window_size - self.step_size} samples)")
        print(f"  Step size: {self.step_size} samples")
        
        X_windows, y_windows, subject_windows = [], [], []
        
        for subject in df['dataset'].unique():
            for activity in df['activity'].unique():
                subset = df[(df['dataset'] == subject) & (df['activity'] == activity)]
                
                if len(subset) < self.window_size:
                    continue
                
                # Sort by time if available
                if 'time_ms' in subset.columns:
                    subset = subset.sort_values('time_ms')
                
                sensor_data = subset[self.sensor_columns].values
                activity_label = self.activities[activity]
                
                # Create sliding windows
                for i in range(0, len(sensor_data) - self.window_size + 1, self.step_size):
                    window = sensor_data[i:i + self.window_size]
                    X_windows.append(window)
                    y_windows.append(activity_label - 1)  # Convert to 0-based index
                    subject_windows.append(subject)
        
        X_windows = np.array(X_windows)
        y_windows = np.array(y_windows)
        subject_windows = np.array(subject_windows)
        
        print(f"  Total windows created: {len(X_windows)}")
        print(f"  Window shape: {X_windows.shape}")
        
        return X_windows, y_windows, subject_windows
    
    def prepare_data(self, dataset_paths):

        # 1. Load combined datasets
        df = self.load_combined_datasets(dataset_paths)
        
        # 2. Clean data
        df_clean = self.clean_data(df)
        
        # 3. Balance dataset
        df_balanced = self.balance_dataset(df_clean, method='smart_balance')
        
        # 4. Create sliding windows
        X_windows, y_windows, subject_windows = self.create_sliding_windows(df_balanced)
        
        # 5. Split and normalize 
        print("\n Normalizing features...")
        scaler = StandardScaler()
       
        unique_subjects = sorted(list(np.unique(subject_windows)))

        n_subjects = len(unique_subjects)
        n_test = max(1, int(n_subjects * 0.15))
        n_val = max(1, int(n_subjects * 0.15))

        test_subjects = unique_subjects[:n_test]
        val_subjects = unique_subjects[n_test:n_test + n_val]
        train_subjects = unique_subjects[n_test + n_val:]

        train_mask = np.isin(subject_windows, train_subjects)
        val_mask = np.isin(subject_windows, val_subjects)
        test_mask = np.isin(subject_windows, test_subjects)

        X_train = X_windows[train_mask]
        y_train = y_windows[train_mask]

        X_val = X_windows[val_mask]
        y_val = y_windows[val_mask]

        X_test = X_windows[test_mask]
        y_test = y_windows[test_mask]

        scaler = StandardScaler()

        X_train_reshaped = X_train.reshape(-1, self.n_features)
        X_train_normalized = scaler.fit_transform(X_train_reshaped)
        X_train = X_train_normalized.reshape(X_train.shape)

        X_val_reshaped = X_val.reshape(-1, self.n_features)
        X_val_normalized = scaler.transform(X_val_reshaped) 
        X_val = X_val_normalized.reshape(X_val.shape)

        X_test_reshaped = X_test.reshape(-1, self.n_features)
        X_test_normalized = scaler.transform(X_test_reshaped)  
        X_test = X_test_normalized.reshape(X_test.shape)
        
        print(f"   Data split summary:")
        print(f"    Training subjects: {', '.join(train_subjects)}")
        print(f"    Validation subjects: {', '.join(val_subjects)}")
        print(f"    Testing subjects: {', '.join(test_subjects)}")
        print(f"    Training windows: {len(X_train)}")
        print(f"    Validation windows: {len(X_val)}")
        print(f"    Testing windows: {len(X_test)}")
        
        # Save preprocessing info
        preprocessing_info = {
            'scaler_mean': scaler.mean_.tolist(),
            'scaler_scale': scaler.scale_.tolist(),
            'window_size': self.window_size,
            'overlap': self.overlap,
            'n_features': self.n_features,
            'n_classes': self.n_classes,
            'activities': {v-1: k for k, v in self.activities.items()},
            'sensor_columns': self.sensor_columns,
            'train_subjects': train_subjects,
            'val_subjects': val_subjects,
        }
        
        with open('combined_preprocessing_info.json', 'w') as f:
            json.dump(preprocessing_info, f, indent=4)
        print("\n Preprocessing info saved to combined_preprocessing_info.json")
        
        return X_train, X_val, X_test, y_train, y_val, y_test, scaler

def main():
    
    # Define paths to your datasets
    base_path = "/home/bnhan2710/source-code/PBL4/AI/dataset"
    dataset_paths = {
        'HUNG': os.path.join(base_path, 'HUNG'),
        'BINH': os.path.join(base_path, 'BINH'),
        'CUONG': os.path.join(base_path, 'CUONG'),
        'NHAN': os.path.join(base_path, 'NHAN'),
        'BACH': os.path.join(base_path, 'BACH')
    }
    
    X_train, X_val, X_test, y_train, y_val, y_test, scaler = loader.prepare_data(dataset_paths)
    loader = Preprocessor()
    

if __name__ == "__main__":
    main()