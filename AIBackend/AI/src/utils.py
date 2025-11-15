import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from sklearn.metrics import classification_report, confusion_matrix, f1_score

def plot_single_cm(cm, activity_names, test_subject, fold_idx, file_suffix="cnn_gru_aug"):
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    plt.figure(figsize=(9, 7))
    sns.heatmap(cm_normalized, annot=True, fmt='.2f', cmap='magma', 
                xticklabels=activity_names, 
                yticklabels=activity_names,
                cbar_kws={'label': 'Proportion'}, vmin=0, vmax=1)
    
    plt.title(f'Normalized Confusion Matrix - Test Subject: {test_subject} (Fold {fold_idx + 1})', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Predicted Activity')
    plt.ylabel('Actual Activity')
    plt.xticks(np.arange(len(activity_names)) + 0.5, activity_names, rotation=45, ha='right')
    plt.yticks(np.arange(len(activity_names)) + 0.5, activity_names, rotation=0)

    plt.tight_layout()
    # Chú ý: Cần tạo thư mục results/cm trong thư mục gốc
    os.makedirs('results/cm', exist_ok=True) 
    save_path = f'results/cm/{test_subject}_cm_{file_suffix}.png'
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"  💾 Saved Confusion Matrix for {test_subject} as {save_path}")
    plt.close() 

def plot_loso_results(all_metrics, activity_names, total_cm, file_suffix="cnn_gru_aug"):
    num_folds = len(all_metrics)
    test_subjects = [m['test_subject'] for m in all_metrics]
    accuracies = [m['test_accuracy'] for m in all_metrics]
    f1_scores = [m['weighted_f1'] for m in all_metrics]
    
    avg_accuracy = np.mean(accuracies)
    avg_f1 = np.mean(f1_scores)
    
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(f'LOSO Cross-Validation Results (N={num_folds} Folds) - {file_suffix.replace("_", " ").upper()}', fontsize=16, fontweight='bold')
    
    x_pos = np.arange(len(test_subjects))
    width = 0.35
    
    axes[0].bar(x_pos - width/2, accuracies, width, label='Test Accuracy', color='teal', alpha=0.8)
    axes[0].bar(x_pos + width/2, f1_scores, width, label='Weighted F1-Score', color='darkorange', alpha=0.8)
    
    axes[0].axhline(avg_accuracy, color='teal', linestyle='--', linewidth=1.5, label=f'Avg Acc: {avg_accuracy:.4f}')
    axes[0].axhline(avg_f1, color='darkorange', linestyle='--', linewidth=1.5, label=f'Avg F1: {avg_f1:.4f}')
    
    axes[0].set_ylabel('Score')
    axes[0].set_title('Performance per Left-Out Subject (Fold)')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(test_subjects, rotation=45, ha='right')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.5)
    axes[0].set_ylim(0, 1.0)
    
    cm_normalized = total_cm.astype('float') / total_cm.sum(axis=1)[:, np.newaxis]
    sns.heatmap(cm_normalized, annot=True, fmt='.2f', cmap='Blues', 
                xticklabels=activity_names, 
                yticklabels=activity_names,
                ax=axes[1],
                cbar_kws={'label': 'Proportion'}, vmin=0, vmax=1)
    axes[1].set_title('Total Normalized Confusion Matrix (Across all Folds)', fontweight='bold', fontsize=12)
    axes[1].set_xlabel('Predicted')
    axes[1].set_ylabel('Actual')
    axes[1].set_xticks(np.arange(len(activity_names)) + 0.5)
    axes[1].set_yticks(np.arange(len(activity_names)) + 0.5)
    axes[1].set_xticklabels(activity_names, rotation=45, ha='right')
    axes[1].set_yticklabels(activity_names, rotation=0)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Chú ý: Cần tạo thư mục results trong thư mục gốc
    os.makedirs('results', exist_ok=True)
    save_path = f'results/loso_cv_results_{file_suffix}.png'
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n💾 LOSO Cross-Validation visualization saved as {save_path}")
    plt.close()

def plot_training_history(history, test_subject, val_subject, fold_idx, file_suffix="cnn_gru_aug"):
    history_df = pd.DataFrame(history.history)
    epochs = range(1, len(history_df) + 1)
    
    plt.figure(figsize=(14, 6))

    plt.subplot(1, 2, 1)
    plt.plot(epochs, history_df['loss'], 'r', label='Training Loss')
    if 'val_loss' in history_df.columns:
        plt.plot(epochs, history_df['val_loss'], 'b', label=f'Validation Loss ({val_subject})')
    plt.title(f'Loss - Fold {fold_idx + 1} (Test={test_subject})', fontsize=14, fontweight='bold')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(axis='y', alpha=0.5)

    plt.subplot(1, 2, 2)
    plt.plot(epochs, history_df['accuracy'], 'r', label='Training Accuracy')
    if 'val_accuracy' in history_df.columns:
        plt.plot(epochs, history_df['val_accuracy'], 'b', label=f'Validation Accuracy ({val_subject})')
    plt.title(f'Accuracy - Fold {fold_idx + 1} (Test={test_subject})', fontsize=14, fontweight='bold')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(axis='y', alpha=0.5)

    plt.tight_layout()
    # Chú ý: Cần tạo thư mục results/history trong thư mục gốc
    os.makedirs('results/history', exist_ok=True)
    save_path = f'results/history/{test_subject}_history_{file_suffix}.png'
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"  💾 Saved Training History for {test_subject} as {save_path}")
    plt.close()