"""
Comprehensive Dataset Analysis for HAR
Analyzes sensor data across different subjects and activities
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (20, 12)
plt.rcParams['font.size'] = 10

class DatasetAnalyzer:
    def __init__(self):
        self.activities = ['WALKING', 'UPSTAIRS', 'DOWNSTAIRS', 'SITTING', 'STANDING', 'RUNNING']
        self.sensor_columns = ['ax_g', 'ay_g', 'az_g', 'gx_dps', 'gy_dps', 'gz_dps']
        self.subjects = ['BACH', 'BINH', 'HUNG', 'NHAN','CUONG','PHONG']
        self.colors = {
            'WALKING': '#8B4513',
            'UPSTAIRS': '#9370DB', 
            'DOWNSTAIRS': '#4169E1',
            'SITTING': '#32CD32',
            'STANDING': '#FF6347',
            'RUNNING': '#FF8C00'
        }
        
    def load_all_data(self, base_path):
        """Load data from all subjects"""
        print("📂 Loading data from all subjects...")
        
        all_data = []
        
        for subject in self.subjects:
            subject_path = os.path.join(base_path, subject)
            if not os.path.exists(subject_path):
                print(f"  ⚠️  {subject} not found")
                continue
                
            for activity in self.activities:
                activity_path = os.path.join(subject_path, activity)
                if not os.path.exists(activity_path):
                    continue
                    
                csv_files = [f for f in os.listdir(activity_path) if f.endswith('.csv')]
                
                for csv_file in csv_files:
                    file_path = os.path.join(activity_path, csv_file)
                    try:
                        df = pd.read_csv(file_path)
                        
                        # Check if required columns exist
                        if not all(col in df.columns for col in self.sensor_columns):
                            continue
                        
                        df['subject'] = subject
                        df['activity'] = activity
                        df['file'] = csv_file
                        
                        all_data.append(df)
                        
                    except Exception as e:
                        print(f"    ❌ Error loading {csv_file}: {e}")
                        continue
        
        if not all_data:
            raise ValueError("No data could be loaded!")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"  ✅ Loaded {len(combined_df)} samples from {combined_df['subject'].nunique()} subjects")
        
        return combined_df
    
    def calculate_magnitude(self, df):
        """Calculate acceleration and gyroscope magnitude"""
        df['accel_mag'] = np.sqrt(df['ax_g']**2 + df['ay_g']**2 + df['az_g']**2)
        df['gyro_mag'] = np.sqrt(df['gx_dps']**2 + df['gy_dps']**2 + df['gz_dps']**2)
        return df
    
    def create_comprehensive_visualization(self, df):
        """Create comprehensive visualization comparing subjects and activities"""
        
        print("\n📊 Creating comprehensive visualizations...")
        
        # Calculate magnitudes
        df = self.calculate_magnitude(df)
        
        fig = plt.figure(figsize=(24, 16))
        
        # ============ 1. Subject Variability: Mean Accel Mag per Activity ============
        ax1 = plt.subplot(3, 4, 1)
        
        pivot_data = df.groupby(['subject', 'activity'])['accel_mag'].mean().reset_index()
        pivot_table = pivot_data.pivot(index='subject', columns='activity', values='accel_mag')
        
        x = np.arange(len(self.subjects))
        width = 0.13
        
        for i, activity in enumerate(self.activities):
            if activity in pivot_table.columns:
                values = [pivot_table.loc[subj, activity] if subj in pivot_table.index else 0 
                         for subj in self.subjects]
                ax1.bar(x + i*width, values, width, label=activity, 
                       color=self.colors.get(activity, 'gray'), alpha=0.8)
        
        ax1.set_xlabel('Subject', fontweight='bold')
        ax1.set_ylabel('Mean Acceleration Magnitude (g)', fontweight='bold')
        ax1.set_title('Subject Variability: Mean Accel Mag per Activity', fontweight='bold', fontsize=12)
        ax1.set_xticks(x + width * 2.5)
        ax1.set_xticklabels(self.subjects)
        ax1.legend(title='Activity', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # ============ 2. Subject Variability: Mean Gyro Mag per Activity ============
        ax2 = plt.subplot(3, 4, 2)
        
        pivot_data_gyro = df.groupby(['subject', 'activity'])['gyro_mag'].mean().reset_index()
        pivot_table_gyro = pivot_data_gyro.pivot(index='subject', columns='activity', values='gyro_mag')
        
        for i, activity in enumerate(self.activities):
            if activity in pivot_table_gyro.columns:
                values = [pivot_table_gyro.loc[subj, activity] if subj in pivot_table_gyro.index else 0 
                         for subj in self.subjects]
                ax2.bar(x + i*width, values, width, label=activity, 
                       color=self.colors.get(activity, 'gray'), alpha=0.8)
        
        ax2.set_xlabel('Subject', fontweight='bold')
        ax2.set_ylabel('Mean Gyroscope Magnitude (dps)', fontweight='bold')
        ax2.set_title('Subject Variability: Mean Gyro Mag per Activity', fontweight='bold', fontsize=12)
        ax2.set_xticks(x + width * 2.5)
        ax2.set_xticklabels(self.subjects)
        ax2.legend(title='Activity', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # ============ 3. Activity Comparison: Accel Magnitude Distribution ============
        ax3 = plt.subplot(3, 4, 3)
        
        activity_order = self.activities
        data_for_box = [df[df['activity'] == act]['accel_mag'].values for act in activity_order]
        
        bp = ax3.boxplot(data_for_box, labels=activity_order, patch_artist=True,
                        showfliers=False, widths=0.6)
        
        for patch, activity in zip(bp['boxes'], activity_order):
            patch.set_facecolor(self.colors.get(activity, 'gray'))
            patch.set_alpha(0.7)
        
        ax3.set_xlabel('Activity', fontweight='bold')
        ax3.set_ylabel('Acceleration Magnitude (g)', fontweight='bold')
        ax3.set_title('Activity Comparison: Accel Magnitude Distribution', fontweight='bold', fontsize=12)
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # ============ 4. Activity Comparison: Gyro Magnitude Distribution ============
        ax4 = plt.subplot(3, 4, 4)
        
        data_for_box_gyro = [df[df['activity'] == act]['gyro_mag'].values for act in activity_order]
        
        bp2 = ax4.boxplot(data_for_box_gyro, labels=activity_order, patch_artist=True,
                         showfliers=False, widths=0.6)
        
        for patch, activity in zip(bp2['boxes'], activity_order):
            patch.set_facecolor(self.colors.get(activity, 'gray'))
            patch.set_alpha(0.7)
        
        ax4.set_xlabel('Activity', fontweight='bold')
        ax4.set_ylabel('Gyroscope Magnitude (dps)', fontweight='bold')
        ax4.set_title('Activity Comparison: Gyro Magnitude Distribution', fontweight='bold', fontsize=12)
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3, axis='y')
        
        # ============ 5. Sample Count per Subject-Activity ============
        ax5 = plt.subplot(3, 4, 5)
        
        count_data = df.groupby(['subject', 'activity']).size().reset_index(name='count')
        count_pivot = count_data.pivot(index='subject', columns='activity', values='count').fillna(0)
        
        im = ax5.imshow(count_pivot.values, cmap='YlOrRd', aspect='auto')
        ax5.set_xticks(range(len(count_pivot.columns)))
        ax5.set_yticks(range(len(count_pivot.index)))
        ax5.set_xticklabels(count_pivot.columns, rotation=45, ha='right')
        ax5.set_yticklabels(count_pivot.index)
        ax5.set_title('Sample Count per Subject-Activity', fontweight='bold', fontsize=12)
        
        # Add text annotations
        for i in range(len(count_pivot.index)):
            for j in range(len(count_pivot.columns)):
                text = ax5.text(j, i, int(count_pivot.values[i, j]),
                              ha="center", va="center", color="black", fontsize=8)
        
        plt.colorbar(im, ax=ax5, label='Number of Samples')
        
        # ============ 6. Coefficient of Variation (CV) - Inter-subject variability ============
        ax6 = plt.subplot(3, 4, 6)
        
        cv_data = []
        for activity in self.activities:
            activity_df = df[df['activity'] == activity]
            subject_means = activity_df.groupby('subject')['accel_mag'].mean()
            cv = (subject_means.std() / subject_means.mean()) * 100 if subject_means.mean() > 0 else 0
            cv_data.append(cv)
        
        bars = ax6.bar(self.activities, cv_data, color=[self.colors.get(act, 'gray') for act in self.activities], alpha=0.7)
        ax6.set_xlabel('Activity', fontweight='bold')
        ax6.set_ylabel('Coefficient of Variation (%)', fontweight='bold')
        ax6.set_title('Inter-Subject Variability (CV of Accel Mag)', fontweight='bold', fontsize=12)
        ax6.tick_params(axis='x', rotation=45)
        ax6.axhline(y=20, color='red', linestyle='--', alpha=0.5, label='High variability (20%)')
        ax6.legend()
        ax6.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, val in zip(bars, cv_data):
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # ============ 7. Signal-to-Noise Ratio per Activity ============
        ax7 = plt.subplot(3, 4, 7)
        
        snr_data = []
        for activity in self.activities:
            activity_df = df[df['activity'] == activity]
            signal_power = activity_df['accel_mag'].mean() ** 2
            noise_power = activity_df['accel_mag'].std() ** 2
            snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 0
            snr_data.append(snr)
        
        ax7.bar(self.activities, snr_data, color=[self.colors.get(act, 'gray') for act in self.activities], alpha=0.7)
        ax7.set_xlabel('Activity', fontweight='bold')
        ax7.set_ylabel('SNR (dB)', fontweight='bold')
        ax7.set_title('Signal-to-Noise Ratio per Activity', fontweight='bold', fontsize=12)
        ax7.tick_params(axis='x', rotation=45)
        ax7.grid(True, alpha=0.3, axis='y')
        
        # ============ 8. Feature Correlation Heatmap ============
        ax8 = plt.subplot(3, 4, 8)
        
        correlation = df[self.sensor_columns + ['accel_mag', 'gyro_mag']].corr()
        
        sns.heatmap(correlation, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                   square=True, ax=ax8, cbar_kws={'label': 'Correlation'})
        ax8.set_title('Feature Correlation Heatmap', fontweight='bold', fontsize=12)
        
        # ============ 9. Mean Acceleration by Axis ============
        ax9 = plt.subplot(3, 4, 9)
        
        axes_data = df.groupby('activity')[['ax_g', 'ay_g', 'az_g']].mean()
        
        x_pos = np.arange(len(self.activities))
        width = 0.25
        
        ax9.bar(x_pos - width, axes_data['ax_g'], width, label='X-axis', color='#FF6B6B', alpha=0.8)
        ax9.bar(x_pos, axes_data['ay_g'], width, label='Y-axis', color='#4ECDC4', alpha=0.8)
        ax9.bar(x_pos + width, axes_data['az_g'], width, label='Z-axis', color='#45B7D1', alpha=0.8)
        
        ax9.set_xlabel('Activity', fontweight='bold')
        ax9.set_ylabel('Mean Acceleration (g)', fontweight='bold')
        ax9.set_title('Mean Acceleration by Axis', fontweight='bold', fontsize=12)
        ax9.set_xticks(x_pos)
        ax9.set_xticklabels(self.activities, rotation=45, ha='right')
        ax9.legend()
        ax9.grid(True, alpha=0.3, axis='y')
        ax9.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # ============ 10. Mean Gyroscope by Axis ============
        ax10 = plt.subplot(3, 4, 10)
        
        gyro_data = df.groupby('activity')[['gx_dps', 'gy_dps', 'gz_dps']].mean()
        
        ax10.bar(x_pos - width, gyro_data['gx_dps'], width, label='X-axis', color='#FF6B6B', alpha=0.8)
        ax10.bar(x_pos, gyro_data['gy_dps'], width, label='Y-axis', color='#4ECDC4', alpha=0.8)
        ax10.bar(x_pos + width, gyro_data['gz_dps'], width, label='Z-axis', color='#45B7D1', alpha=0.8)
        
        ax10.set_xlabel('Activity', fontweight='bold')
        ax10.set_ylabel('Mean Gyroscope (dps)', fontweight='bold')
        ax10.set_title('Mean Gyroscope by Axis', fontweight='bold', fontsize=12)
        ax10.set_xticks(x_pos)
        ax10.set_xticklabels(self.activities, rotation=45, ha='right')
        ax10.legend()
        ax10.grid(True, alpha=0.3, axis='y')
        ax10.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # ============ 11. Standard Deviation per Activity (Accel) ============
        ax11 = plt.subplot(3, 4, 11)
        
        std_data = df.groupby('activity')['accel_mag'].std()
        
        ax11.bar(self.activities, std_data.values, 
                color=[self.colors.get(act, 'gray') for act in self.activities], alpha=0.7)
        ax11.set_xlabel('Activity', fontweight='bold')
        ax11.set_ylabel('Std Dev of Accel Magnitude (g)', fontweight='bold')
        ax11.set_title('Activity Variability (Std Dev)', fontweight='bold', fontsize=12)
        ax11.tick_params(axis='x', rotation=45)
        ax11.grid(True, alpha=0.3, axis='y')
        
        # ============ 12. Data Quality Summary ============
        ax12 = plt.subplot(3, 4, 12)
        ax12.axis('off')
        
        # Calculate statistics
        total_samples = len(df)
        samples_per_subject = df.groupby('subject').size()
        samples_per_activity = df.groupby('activity').size()
        
        # Calculate separability score (simplified)
        activity_means = df.groupby('activity')['accel_mag'].mean()
        overall_mean = df['accel_mag'].mean()
        between_var = ((activity_means - overall_mean) ** 2).mean()
        within_var = df.groupby('activity')['accel_mag'].var().mean()
        separability = between_var / within_var if within_var > 0 else 0
        
        # Calculate balance score
        activity_counts = df.groupby('activity').size()
        balance_score = (activity_counts.min() / activity_counts.max()) * 100
        
        summary_text = f"""
        DATA QUALITY SUMMARY
        {'='*40}
        
        Total Samples: {total_samples:,}
        Subjects: {df['subject'].nunique()}
        Activities: {df['activity'].nunique()}
        
        Samples per Subject:
        {samples_per_subject.to_string()}
        
        Samples per Activity:
        {samples_per_activity.to_string()}
        
        QUALITY METRICS:
        • Class Balance: {balance_score:.1f}%
        • Separability Score: {separability:.3f}
        • Mean Accel Range: {df['accel_mag'].min():.2f} - {df['accel_mag'].max():.2f} g
        • Mean Gyro Range: {df['gyro_mag'].min():.2f} - {df['gyro_mag'].max():.2f} dps
        
        RECOMMENDATIONS:
        {'✅ Good class balance' if balance_score > 80 else '⚠️  Consider balancing classes'}
        {'✅ Good separability' if separability > 0.5 else '⚠️  Low separability - challenging'}
        """
        
        ax12.text(0.1, 0.9, summary_text, transform=ax12.transAxes,
                 fontsize=10, verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        plt.tight_layout()
        plt.savefig('comprehensive_dataset_analysis.png', dpi=300, bbox_inches='tight')
        print("  ✅ Saved: comprehensive_dataset_analysis.png")
        
        return fig
    
    def create_subject_comparison(self, df):
        """Create detailed subject comparison plots"""
        
        print("\n📊 Creating subject comparison visualization...")
        
        df = self.calculate_magnitude(df)
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('Subject-wise Activity Comparison', fontsize=16, fontweight='bold')
        
        for idx, subject in enumerate(self.subjects):
            row = idx // 3
            col = idx % 3
            ax = axes[row, col]
            
            subject_data = df[df['subject'] == subject]
            
            # Calculate mean for each activity
            activity_means = subject_data.groupby('activity')['accel_mag'].mean()
            activity_stds = subject_data.groupby('activity')['accel_mag'].std()
            
            activities = activity_means.index.tolist()
            means = activity_means.values
            stds = activity_stds.values
            
            colors_list = [self.colors.get(act, 'gray') for act in activities]
            
            bars = ax.bar(range(len(activities)), means, yerr=stds, 
                         color=colors_list, alpha=0.7, capsize=5)
            
            ax.set_xlabel('Activity', fontweight='bold')
            ax.set_ylabel('Mean Accel Magnitude (g)', fontweight='bold')
            ax.set_title(f'{subject}', fontweight='bold', fontsize=12)
            ax.set_xticks(range(len(activities)))
            ax.set_xticklabels(activities, rotation=45, ha='right')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add sample counts
            for i, (bar, activity) in enumerate(zip(bars, activities)):
                count = len(subject_data[subject_data['activity'] == activity])
                ax.text(i, bar.get_height() + stds[i], f'n={count}',
                       ha='center', va='bottom', fontsize=8)
        
        # Remove empty subplot if odd number of subjects
        if len(self.subjects) % 3 != 0:
            fig.delaxes(axes[1, 2])
        
        plt.tight_layout()
        plt.savefig('subject_comparison_detailed.png', dpi=300, bbox_inches='tight')
        print("  ✅ Saved: subject_comparison_detailed.png")
        
        return fig
    
    def generate_report(self, df):
        """Generate comprehensive text report"""
        
        print("\n📄 Generating analysis report...")
        
        df = self.calculate_magnitude(df)
        
        report = []
        report.append("="*80)
        report.append("COMPREHENSIVE DATASET ANALYSIS REPORT")
        report.append("="*80)
        report.append("")
        
        # Overall Statistics
        report.append("1. OVERALL STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Samples: {len(df):,}")
        report.append(f"Number of Subjects: {df['subject'].nunique()}")
        report.append(f"Number of Activities: {df['activity'].nunique()}")
        report.append(f"Number of Files: {df['file'].nunique()}")
        report.append("")
        
        # Per-Subject Statistics
        report.append("2. PER-SUBJECT STATISTICS")
        report.append("-" * 40)
        for subject in self.subjects:
            subject_df = df[df['subject'] == subject]
            if len(subject_df) > 0:
                report.append(f"\n{subject}:")
                report.append(f"  Total samples: {len(subject_df):,}")
                report.append(f"  Activities recorded: {subject_df['activity'].nunique()}")
                report.append(f"  Mean accel magnitude: {subject_df['accel_mag'].mean():.3f} ± {subject_df['accel_mag'].std():.3f} g")
                report.append(f"  Mean gyro magnitude: {subject_df['gyro_mag'].mean():.3f} ± {subject_df['gyro_mag'].std():.3f} dps")
        report.append("")
        
        # Per-Activity Statistics
        report.append("3. PER-ACTIVITY STATISTICS")
        report.append("-" * 40)
        for activity in self.activities:
            activity_df = df[df['activity'] == activity]
            if len(activity_df) > 0:
                report.append(f"\n{activity}:")
                report.append(f"  Total samples: {len(activity_df):,}")
                report.append(f"  Subjects: {activity_df['subject'].nunique()}")
                report.append(f"  Mean accel magnitude: {activity_df['accel_mag'].mean():.3f} ± {activity_df['accel_mag'].std():.3f} g")
                report.append(f"  Mean gyro magnitude: {activity_df['gyro_mag'].mean():.3f} ± {activity_df['gyro_mag'].std():.3f} dps")
                
                # Inter-subject variability
                subject_means = activity_df.groupby('subject')['accel_mag'].mean()
                cv = (subject_means.std() / subject_means.mean()) * 100 if subject_means.mean() > 0 else 0
                report.append(f"  Inter-subject CV: {cv:.1f}%")
        report.append("")
        
        # Data Quality Assessment
        report.append("4. DATA QUALITY ASSESSMENT")
        report.append("-" * 40)
        
        # Class balance
        activity_counts = df.groupby('activity').size()
        balance_ratio = activity_counts.min() / activity_counts.max()
        report.append(f"Class Balance Ratio: {balance_ratio:.3f} ({balance_ratio*100:.1f}%)")
        if balance_ratio > 0.8:
            report.append("  ✅ GOOD: Classes are well balanced")
        elif balance_ratio > 0.5:
            report.append("  ⚠️  FAIR: Some class imbalance present")
        else:
            report.append("  ❌ POOR: Significant class imbalance")
        report.append("")
        
        # Separability
        activity_means = df.groupby('activity')['accel_mag'].mean()
        overall_mean = df['accel_mag'].mean()
        between_var = ((activity_means - overall_mean) ** 2).mean()
        within_var = df.groupby('activity')['accel_mag'].var().mean()
        separability = between_var / within_var if within_var > 0 else 0
        
        report.append(f"Class Separability Score: {separability:.3f}")
        if separability > 1.0:
            report.append("  ✅ EXCELLENT: Activities are well separated")
        elif separability > 0.5:
            report.append("  ✅ GOOD: Activities are reasonably separable")
        elif separability > 0.2:
            report.append("  ⚠️  FAIR: Some overlap between activities")
        else:
            report.append("  ❌ POOR: High overlap - challenging classification")
        report.append("")
        
        # Subject consistency
        report.append("Subject Consistency Analysis:")
        for activity in self.activities:
            activity_df = df[df['activity'] == activity]
            if len(activity_df) > 0:
                subject_means = activity_df.groupby('subject')['accel_mag'].mean()
                cv = (subject_means.std() / subject_means.mean()) * 100 if subject_means.mean() > 0 else 0
                report.append(f"  {activity}: CV = {cv:.1f}%")
        report.append("")
        
        # Recommendations
        report.append("5. RECOMMENDATIONS FOR MODEL TRAINING")
        report.append("-" * 40)
        
        if balance_ratio < 0.7:
            report.append("• Apply class balancing techniques (oversampling/undersampling)")
        
        if separability < 0.5:
            report.append("• Use more complex model architecture")
            report.append("• Consider feature engineering")
            report.append("• Apply data augmentation")
        
        # Check for high variability activities
        for activity in self.activities:
            activity_df = df[df['activity'] == activity]
            if len(activity_df) > 0:
                subject_means = activity_df.groupby('subject')['accel_mag'].mean()
                cv = (subject_means.std() / subject_means.mean()) * 100 if subject_means.mean() > 0 else 0
                if cv > 30:
                    report.append(f"• {activity} shows high inter-subject variability (CV={cv:.1f}%) - consider subject-specific normalization")
        
        report.append("• Use sequence-based splitting to prevent data leakage")
        report.append("• Consider using time-series specific augmentation")
        
        # Dataset suitability
        report.append("")
        report.append("6. DATASET SUITABILITY FOR HAR")
        report.append("-" * 40)
        
        suitability_score = 0
        max_score = 5
        
        if balance_ratio > 0.7:
            suitability_score += 1
            report.append("✅ Good class balance")
        else:
            report.append("⚠️  Class imbalance present")
        
        if separability > 0.5:
            suitability_score += 1
            report.append("✅ Good class separability")
        else:
            report.append("⚠️  Low separability")
        
        if len(df) > 50000:
            suitability_score += 1
            report.append("✅ Sufficient data volume")
        else:
            report.append("⚠️  Limited data volume")
        
        if df['subject'].nunique() >= 4:
            suitability_score += 1
            report.append("✅ Multiple subjects for generalization")
        else:
            report.append("⚠️  Limited subject diversity")
        
        mean_cv = np.mean([
            (activity_df.groupby('subject')['accel_mag'].mean().std() / 
             activity_df.groupby('subject')['accel_mag'].mean().mean()) * 100
            for activity in self.activities
            if (activity_df := df[df['activity'] == activity]).groupby('subject').size().min() > 0
        ])
        
        if mean_cv < 30:
            suitability_score += 1
            report.append("✅ Consistent patterns across subjects")
        else:
            report.append("⚠️  High inter-subject variability")
        
        report.append("")
        report.append(f"OVERALL SUITABILITY: {suitability_score}/{max_score}")
        
        if suitability_score >= 4:
            report.append("🎉 EXCELLENT - Dataset is well-suited for HAR training")
        elif suitability_score >= 3:
            report.append("👍 GOOD - Dataset can be used with some preprocessing")
        elif suitability_score >= 2:
            report.append("⚠️  FAIR - Consider collecting more data or balancing classes")
        else:
            report.append("❌ POOR - Dataset may need significant improvements")
        
        report.append("")
        report.append("="*80)
        
        # Save report
        report_text = "\n".join(report)
        with open('dataset_analysis_report.txt', 'w') as f:
            f.write(report_text)
        
        print("  ✅ Saved: dataset_analysis_report.txt")
        print("\n" + report_text)
        
        return report_text

def main():
    """Main function"""
    
    print("🚀 Starting Comprehensive Dataset Analysis")
    print("="*80)
    
    base_path = '/home/bnhan2710/source-code/PBL4/AI/dataset'
    
    analyzer = DatasetAnalyzer()
    
    # Load data
    df = analyzer.load_all_data(base_path)
    
    # Create visualizations
    analyzer.create_comprehensive_visualization(df)
    analyzer.create_subject_comparison(df)
    
    # Generate report
    analyzer.generate_report(df)
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nGenerated files:")
    print("  📊 comprehensive_dataset_analysis.png")
    print("  📊 subject_comparison_detailed.png")
    print("  📄 dataset_analysis_report.txt")

if __name__ == "__main__":
    main()
