import numpy as np
from scipy.interpolate import CubicSpline 

def time_warping(X, sigma=0.2):
    """Áp dụng Time Warping."""
    N, T, F = X.shape
    tt = np.arange(T)
    num_knots = 4
    X_warped = np.zeros_like(X)
    
    for j in range(N):
        knots = np.linspace(0, T-1, num_knots)
        y_knots = knots + np.random.normal(0, sigma * T, size=num_knots)
        y_knots = np.clip(y_knots, 0, T-1) 
        spline = CubicSpline(knots, y_knots)
        warped_time = spline(tt)
        
        for i in range(F): 
            X_warped[j, :, i] = np.interp(warped_time, tt, X[j, :, i])
            
    return X_warped

def magnitude_scaling(X, sigma=0.1):
    """Áp dụng Magnitude Scaling (Giảm sự nhạy cảm với biên độ)."""
    N, T, F = X.shape
    scaling_factors = np.random.normal(loc=1.0, scale=sigma, size=(N, F))
    # Sử dụng np.newaxis để broadcast đúng cách
    X_scaled = X * scaling_factors[:, np.newaxis, :] 
    return X_scaled

def jittering(X, jitter_std=0.05):
    """Áp dụng Jittering (thêm nhiễu Gaussian)."""
    noise = np.random.normal(0, jitter_std, size=X.shape)
    return X + noise


def augment_data_improved(X_batch, y_batch, ratio_jitter=0.5, ratio_warp=0.25, ratio_scale=0.25):
    """Augmentation tổng hợp."""
    N = X_batch.shape[0]
    X_augmented = []
    y_augmented = []
    
    ratio_total = ratio_jitter + ratio_warp + ratio_scale
    if ratio_total == 0:
        return X_batch, y_batch

    num_jitter = int(N * ratio_jitter)
    num_warp = int(N * ratio_warp)
    num_scale = int(N * ratio_scale)
    
    if num_jitter > 0:
        indices = np.random.choice(N, size=num_jitter, replace=True)
        # Tạo bản sao (.copy()) để tránh thay đổi dữ liệu gốc
        X_augmented.append(jittering(X_batch[indices].copy(), jitter_std=0.03)) 
        y_augmented.append(y_batch[indices].copy())
        
    if num_warp > 0:
        indices = np.random.choice(N, size=num_warp, replace=True)
        X_augmented.append(time_warping(X_batch[indices].copy(), sigma=0.05))
        y_augmented.append(y_batch[indices].copy())

    if num_scale > 0:
        indices = np.random.choice(N, size=num_scale, replace=True)
        X_augmented.append(magnitude_scaling(X_batch[indices].copy(), sigma=0.05))
        y_augmented.append(y_batch[indices].copy())

    # Kết hợp dữ liệu gốc và dữ liệu tăng cường
    X_combined = np.concatenate([X_batch] + X_augmented, axis=0)
    y_combined = np.concatenate([y_batch] + y_augmented, axis=0)
    
    return X_combined, y_combined