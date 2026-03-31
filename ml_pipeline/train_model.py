# SPDX-License-Identifier: MIT
import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Create artifact paths
os.makedirs("model_export", exist_ok=True)

# 1. Generate Synthetic Data matching Nira ESP32 Sensor format
# Fields: time_ms, CH1_raw, CH4_raw, Diff_C1_C4, Temp_C
print("Generating synthetic sensor data for training...")
n_samples = 1000

# Base realistic values
time_ms = np.linspace(0, 100000, n_samples)
temp_c = np.random.normal(25.0, 2.0, n_samples)

# Simulate Clean Water (Label 0) vs Microplastics (Label 1)
labels = np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3])

# Diff C1-C4 reacts to microplastics (higher variance and slight capacitance shift)
diff_c1_c4 = np.random.normal(0, 0.1, n_samples)
diff_c1_c4 += labels * np.random.normal(0.5, 0.2, n_samples) # Signal characteristic of MPs

# Adding temperature drift which we already compensated in firmware, 
# but model might use it if residual drift exists.
ch1_raw = 5.0 + diff_c1_c4/2 + temp_c * 0.01 
ch4_raw = 5.0 - diff_c1_c4/2 + temp_c * 0.01

df = pd.DataFrame({
    'time_ms': time_ms,
    'ch1_raw': ch1_raw,
    'ch4_raw': ch4_raw,
    'diff_c1_c4': diff_c1_c4,
    'temp_c': temp_c,
    'label': labels
})

# 2. Feature Engineering
print("Engineering features...")
X = df[['diff_c1_c4', 'temp_c']]  # Using differential capacitance and temperature
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Train Model
print("Training Random Forest Classifier...")
clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
clf.fit(X_train, y_train)

# 4. Evaluate
y_pred = clf.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {acc * 100:.2f}%")
print("Classification Report:")
print(classification_report(y_test, y_pred))

# 5. Export Model for Edge Deployment (or Offline use)
model_path = "model_export/nira_mp_rf_model.pkl"
joblib.dump(clf, model_path)
print(f"Model successfully exported to {model_path}.")
print("To use with ESP32 or MicroPython, consider converting to TFLite or C-array (emlearn).")
