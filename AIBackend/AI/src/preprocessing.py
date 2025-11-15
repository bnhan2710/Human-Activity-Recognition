import numpy as np
import pandas as pd
import os
import warnings
from sklearn.preprocessing import QuantileTransformer, StandardScaler

warnings.filterwarnings('ignore')

class Preprocessor:
    def __init__(self):
        self.activities = {
            'WALKING': 1, 'UPSTAIRS': 2, 'DOWNSTAIRS': 3,
            'SITTING': 4, 'STANDING': 5, 'RUNNING': 6
        }
        self.activity_names = list(self.activities.keys())
        self.n_classes = len(self.activities)
        
        self.sensor_columns = [
            'ax_g', 'ay_g', 'az_g', 'gx_dps', 'gy_dps', 'gz_dps',     
            'amag_g', 'pitch_kf', 'roll_kf'
        ]
        self.derivative_columns = ['d_pitch_kf', 'd_roll_kf']
        self.all_feature_columns = self.sensor_columns + self.derivative_columns
        self.n_features_raw = len(self.sensor_columns)
        self.n_features = len(self.all_feature_columns)

        self.window_size = 40 # 2s at 20Hz
        self.overlap = 0.5
        self.step_size = int(self.window_size * (1 - self.overlap))
        
    def load_single_dataset(self, dataset_path, dataset_name):
        all_data = []
        activity_counts = {}
        
        for activity in self.activities.keys():
            activity_path = os.path.join(dataset_path, activity)
            if not os.path.exists(activity_path):
                continue
                
            activity_data = []
            csv_files = [f for f in os.listdir(activity_path) if f.endswith('.csv')]
            
            for csv_file in csv_files:
                file_path = os.path.join(activity_path, csv_file)
                try:
                    df = pd.read_csv(file_path)
                    missing_cols = [col for col in self.sensor_columns if col not in df.columns]
                    if missing_cols:
                        continue
                    
                    df['activity'] = activity
                    df['dataset'] = dataset_name
                    df['subject'] = dataset_name
                    
                    # Tính đạo hàm (features vững vàng)
                    df['d_pitch_kf'] = df['pitch_kf'].diff().fillna(0)
                    df['d_roll_kf'] = df['roll_kf'].diff().fillna(0)
                    
                    activity_data.append(df)
                    
                except Exception as e:
                    # print(f"Error loading {file_path}: {e}")
                    continue
            
            if activity_data:
                combined_activity = pd.concat(activity_data, ignore_index=True)
                all_data.append(combined_activity)
                activity_counts[activity] = len(combined_activity)
        
        if all_data:
            dataset_df = pd.concat(all_data, ignore_index=True)
            return dataset_df, activity_counts
        else:
            return None, {}
    
    def load_combined_datasets(self, dataset_paths):
        print(f" ⏳ Loading {len(dataset_paths)} datasets...")
        
        all_datasets = []
        
        for dataset_name, dataset_path in dataset_paths.items():
            if dataset_path and os.path.exists(dataset_path):
                data, _ = self.load_single_dataset(dataset_path, dataset_name) 
                if data is not None:
                    all_datasets.append(data)
            else:
                print(f" Skipping {dataset_name}: path not found or invalid")
        
        if not all_datasets:
            raise ValueError(" No datasets could be loaded!")
            
        combined_df = pd.concat(all_datasets, ignore_index=True)
            
        return combined_df
    
    def clean_data(self, df):
        initial_size = len(df)
        print(f"\n🧹 Cleaning data (initial size: {initial_size})...")
        df_clean = df.dropna(subset=self.all_feature_columns)
        
        # Loại bỏ outliers dựa trên IQR
        for col in self.sensor_columns:
            Q1 = df_clean[col].quantile(0.05)
            Q3 = df_clean[col].quantile(0.95)
            IQR = Q3 - Q1
            lower_bound = Q1 - 5.0 * IQR
            upper_bound = Q3 + 5.0 * IQR
            df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]
        
        final_size = len(df_clean)
        print(f"  ✨ Cleaning complete. Final size: {final_size} ({(final_size/initial_size)*100:.1f}% retained)")
        return df_clean
    
    def balance_dataset(self, df, method='smart_balance'):
        print(f"\n⚖️ Smart balancing dataset...")
        activity_counts = df['activity'].value_counts()
        median_count = int(activity_counts.median())
        max_allowed = int(median_count * 2.5)  
        
        balanced_dfs = []
        for activity in df['activity'].unique():
            activity_df = df[df['activity'] == activity]
            current_count = len(activity_df)
            
            if current_count > max_allowed:
                activity_df = activity_df.sample(n=max_allowed, random_state=42)
            elif current_count < median_count * 0.5:
                target = int(median_count * 0.8)
                additional = target - current_count
                extra_df = activity_df.sample(n=additional, replace=True, random_state=42)
                activity_df = pd.concat([activity_df, extra_df], ignore_index=True)
            
            balanced_dfs.append(activity_df)
        
        balanced_df = pd.concat(balanced_dfs, ignore_index=True)
        print(f"  Total samples after balancing: {len(balanced_df)}")
        return balanced_df
    
    def create_sliding_windows(self, df, feature_extraction=False):
        X_windows, y_windows, subject_windows = [], [], []
        data_columns = self.all_feature_columns
        
        for subject in df['dataset'].unique():
            for activity in df['activity'].unique():
                subset = df[(df['dataset'] == subject) & (df['activity'] == activity)]
                if len(subset) < self.window_size:
                    continue
                if 'time_ms' in subset.columns:
                    # Sắp xếp theo thời gian để đảm bảo chuỗi thời gian liên tục
                    subset = subset.sort_values('time_ms')
                
                sensor_data = subset[data_columns].values
                activity_label = self.activities[activity]
                
                for i in range(0, len(sensor_data) - self.window_size + 1, self.step_size):
                    window = sensor_data[i:i + self.window_size]
                    X_windows.append(window) 
                    y_windows.append(activity_label - 1)
                    subject_windows.append(subject)
        
        X_windows = np.array(X_windows)
        y_windows = np.array(y_windows)
        subject_windows = np.array(subject_windows)
        self.n_features = X_windows.shape[2] 
        print(f"  Window shape (N, T, F={self.n_features}): {X_windows.shape}")
        return X_windows, y_windows, subject_windows
    
    def prepare_data(self, dataset_paths, feature_extraction=False, test_subject_name=None, val_subject_name=None):
        # 1️⃣ Load toàn bộ dữ liệu
        df = self.load_combined_datasets(dataset_paths)
        
        # 2️⃣ Lấy danh sách subject (dataset_name = subject)
        unique_subjects = sorted(list(df['dataset'].unique()))
        if test_subject_name not in unique_subjects or val_subject_name not in unique_subjects or test_subject_name == val_subject_name:
            raise ValueError("Invalid subject split configuration.")
        
        train_subjects = [s for s in unique_subjects if s not in [test_subject_name, val_subject_name]]
        test_subject = test_subject_name
        val_subject = val_subject_name

        # 3️⃣ Chia dữ liệu theo subject
        df_train = df[df['dataset'].isin(train_subjects)]
        df_val   = df[df['dataset'] == val_subject]
        df_test  = df[df['dataset'] == test_subject]

        print(f"\n📂 Subjects split:")
        print(f"  Train: {train_subjects}")
        print(f"  Val:   {val_subject}")
        print(f"  Test:  {test_subject}")

        # 4️⃣ Làm sạch dữ liệu (cleaning)
        df_train = self.clean_data(df_train)
        df_val   = self.clean_data(df_val)
        df_test  = self.clean_data(df_test)

        # 5️⃣ Cân bằng dữ liệu — chỉ áp dụng trên train
        df_train = self.balance_dataset(df_train)

        # 6️⃣ Tạo sliding windows cho từng tập
        print("\n🪟 Creating sliding windows...")
        X_train, y_train, _ = self.create_sliding_windows(df_train, feature_extraction)
        X_val,   y_val,   _ = self.create_sliding_windows(df_val,   feature_extraction)
        X_test,  y_test,  _ = self.create_sliding_windows(df_test,  feature_extraction)

        # 7️⃣ Tách feature gốc và đạo hàm
        X_train_raw_9 = X_train[:, :, :self.n_features_raw]
        X_val_raw_9   = X_val[:, :, :self.n_features_raw]
        X_test_raw_9  = X_test[:, :, :self.n_features_raw]

        X_train_deriv_2 = X_train[:, :, self.n_features_raw:]
        X_val_deriv_2   = X_val[:, :, self.n_features_raw:]
        X_test_deriv_2  = X_test[:, :, self.n_features_raw:]

        # 8️⃣ QuantileTransformer (fit chỉ trên train)
        print("\n📏 Applying QuantileTransformer (fit on train only)...")
        qt = QuantileTransformer(output_distribution='normal', n_quantiles=1000, random_state=42)
        qt.fit(X_train_raw_9.reshape(-1, X_train_raw_9.shape[-1]))

        X_train_raw_9 = qt.transform(X_train_raw_9.reshape(-1, X_train_raw_9.shape[-1])).reshape(X_train_raw_9.shape)
        X_val_raw_9   = qt.transform(X_val_raw_9.reshape(-1, X_val_raw_9.shape[-1])).reshape(X_val_raw_9.shape)
        X_test_raw_9  = qt.transform(X_test_raw_9.reshape(-1, X_test_raw_9.shape[-1])).reshape(X_test_raw_9.shape)

        # 9️⃣ Kết hợp lại 11 features
        X_train_combined = np.concatenate([X_train_raw_9, X_train_deriv_2], axis=2)
        X_val_combined   = np.concatenate([X_val_raw_9,   X_val_deriv_2],   axis=2)
        X_test_combined  = np.concatenate([X_test_raw_9,  X_test_deriv_2],  axis=2)

        # 🔟 StandardScaler (fit chỉ trên train)
        print("\n⚙️ Normalizing features with StandardScaler (fit on train only)...")
        scaler = StandardScaler()
        scaler.fit(X_train_combined.reshape(-1, self.n_features))

        X_train = scaler.transform(X_train_combined.reshape(-1, self.n_features)).reshape(X_train_combined.shape)
        X_val   = scaler.transform(X_val_combined.reshape(-1, self.n_features)).reshape(X_val_combined.shape)
        X_test  = scaler.transform(X_test_combined.reshape(-1, self.n_features)).reshape(X_test_combined.shape)

        print(f"\n✅ Data preparation complete.")
        print(f"   Train windows: {len(X_train)}")
        print(f"   Val windows:   {len(X_val)}")
        print(f"   Test windows:  {len(X_test)}")

        return X_train, X_val, X_test, y_train, y_val, y_test, scaler