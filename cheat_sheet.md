
# 1. Clone and setup the project (run only once)

git clone https://github.com/only-foss/Project-Nira.git
cd Project-Nira
git checkout develop


# 2. Install PlatformIO and setup Python environment

pip install platformio

# Run the project's setup script (recommended)
chmod +x setup.sh
./setup.sh

# Activate the virtual environment
source .venv/bin/activate


# 3. Flash the Firmware to ESP32-S3

cd firmware/v1.5_esp32_sensor          # Change to v1.0_esp32_fdc1004 if you built v1.0
pio run -e esp32doit-devkit-v1 -t upload -t monitor


# 4. Run Python Dashboard → Live Analysis

cd ../../                              # Go back to project root
python python/nira_dashboard.py        # This starts Live Analysis (real-time graphs from sensor)


# 5. Post Analysis (Run after recording data)

# After recording data in the dashboard, you can run post analysis using these (if available):

# Option A: Using nira_reader for offline analysis
python python/nira_reader.py

# Option B: Check ml_pipeline for deeper ML-based post analysis
cd ml_pipeline
ls                                     # See available scripts
# Example (replace with actual filename if found):
# python process_recorded_data.py
