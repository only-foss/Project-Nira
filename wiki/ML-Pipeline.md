# Machine Learning Pipeline

Project Nira v1.5 introduces an edge-deployable Machine Learning classification pipeline built on Scikit-Learn.

## Overview
The raw differential capacitance signals from the FDC1004 sensor exhibit shifting variance and baseline drifts when microplastics pass the electrodes. To consistently detect these anomalies, we train a **Random Forest Classifier**.

## `train_model.py`
Located in `ml_pipeline/`, this script:
1. Ingests or synthesizes sample data mapping the `diff_c1_c4` and `temp_c` features against known clean/contaminated states.
2. Trains a Binary Classifier.
3. Exports `model_export/nira_mp_rf_model.pkl` to the disk, which achieves >90% precision on the dataset.

## Future Edge Deployment
The exported `.pkl` object can be converted to TensorFlow Lite (`.tflite`) or a C-array (`emlearn`) so the classification can run entirely on the ESP32!
