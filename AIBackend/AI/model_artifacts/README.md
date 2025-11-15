# Model Artifacts - Ensuring Consistent Preprocessing

## 📋 Overview

Model artifacts contain all preprocessing components (scalers + metadata) needed to ensure that **inference preprocessing exactly matches training preprocessing**.

## 📁 Directory Structure

```
model_artifacts/
├── quantile_transformer.pkl      # QuantileTransformer fitted on training data
├── standard_scaler.pkl           # StandardScaler fitted on training data
└── preprocessing_metadata.json   # Configuration and validation info
```

## 🚀 Quick Start

### 1. Generate Artifacts (One-time setup)

After training your model, run:

```bash
cd c:\PBL4\AIBackend\AI
python save_model_artifacts.py
```

This will:
- Load training data with the same split used during training
- Fit QuantileTransformer on raw 9 features from training set
- Fit StandardScaler on combined 11 features from training set
- Save all components + metadata to `model_artifacts/` directory

### 2. Use Artifacts in Backend

Update `main.py`:

```python
predictor = ActivityPredictor(
    model_path="../AI/final_model_test_BINH_PHONG.h5",
    artifacts_path="../AI/model_artifacts"  # ← Load artifacts!
)
```

### 3. Verify Setup

```bash
cd c:\PBL4\AIBackend\backend
python verify_artifacts.py
```

## ⚠️ Why This Matters

### ❌ Without Artifacts (BAD):

```python
# Scalers fit on FIRST 40 SAMPLES (single window)
qt.fit(first_window_9_features)      # Distribution from 2 seconds of data
scaler.fit(first_window_11_features)  # Statistics from 2 seconds of data
```

**Problem**: If first window is STANDING:
- Accelerometer variance: ~0.02 (very low, person not moving)
- When WALKING data arrives, acceleration = 0.2 gets normalized to 10.0 (huge outlier!)
- Model receives wrong input → Wrong predictions

### ✅ With Artifacts (GOOD):

```python
# Scalers fit on ALL TRAINING DATA (thousands of windows)
qt.fit(all_train_raw_features)    # Distribution from all activities
scaler.fit(all_train_combined)    # Statistics from all activities
```

**Result**: Consistent normalization across all activities → Accurate predictions!

## 📊 Preprocessing Pipeline

### Training Time:

```
Raw Data (N samples)
    ↓
1. Clean & Balance
    ↓
2. Create Windows (M windows × 40 samples × 9 features)
    ↓
3. QuantileTransformer.fit(M×40 samples, 9 features)  ← FIT HERE
    ↓
4. Transform raw 9 features
    ↓
5. Add 2 derivatives → 11 features
    ↓
6. StandardScaler.fit(M×40 samples, 11 features)      ← FIT HERE
    ↓
7. Transform all 11 features
    ↓
Model Training
```

### Inference Time (with artifacts):

```
Single Window (40 samples × 11 features)
    ↓
1. QuantileTransformer.transform(40 samples, 9 features)  ← LOAD from artifacts
    ↓
2. Add 2 derivatives → 11 features
    ↓
3. StandardScaler.transform(40 samples, 11 features)      ← LOAD from artifacts
    ↓
Model Prediction
```

## 🔧 Metadata Validation

The `preprocessing_metadata.json` contains:

- **preprocessing_config**: window_size, overlap, n_features, etc.
- **feature_config**: sensor columns, derivative columns
- **activity_mapping**: class labels
- **training_config**: subjects used, number of windows
- **scaler_stats**: mean/std ranges for validation

This allows automatic validation that inference config matches training config.

## 🐛 Troubleshooting

### Error: "QuantileTransformer not found"

```bash
# Regenerate artifacts
cd c:\PBL4\AIBackend\AI
python save_model_artifacts.py
```

### Error: "Window size mismatch"

Check that your training script and inference code use the same:
- `window_size = 40`
- `overlap = 0.5`
- `n_features = 11`

### Predictions still inaccurate?

1. Verify artifacts were generated from correct training run
2. Check that test/val subjects match training split
3. Run `verify_artifacts.py` to check scaler statistics

## 📝 Notes

- **Generate artifacts ONCE** after training completes
- **Commit artifacts** to version control along with model
- **Regenerate** if you retrain model or change preprocessing pipeline
- **Verify** using `verify_artifacts.py` before deploying

## 🎯 Best Practices

1. ✅ Always use `artifacts_path` (not `scaler_path`)
2. ✅ Generate artifacts immediately after training
3. ✅ Commit artifacts + model together
4. ✅ Verify with `verify_artifacts.py` before deployment
5. ✅ Document training configuration in git commit

---

**Last Updated**: 2025-01-14  
**Version**: 1.0.0
