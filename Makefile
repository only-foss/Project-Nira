.PHONY: all setup test lint build run clean
.DEFAULT_GOAL := all

PYTHON = python3
PIP = pip3
VENV = .venv
BIN = $(VENV)/bin
ESP32_DIR = firmware/v1.5_esp32_fdc1004/Project-Nira

all: setup 

setup:
	@echo "==> Setting up Python virtual environment"
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt

lint:
	@echo "==> Running Python linters"
	$(BIN)/flake8 python/ ml_pipeline/
	$(BIN)/bandit -r python/ ml_pipeline/

run-gui: setup
	@echo "==> Running Nira Dashboard"
	$(BIN)/python main.py

run-cli: setup
	@echo "==> Running Nira Headless Mode"
	$(BIN)/python main.py --cli

train-model: setup
	@echo "==> Training ML Prediction Model"
	$(BIN)/python ml_pipeline/train_model.py

flash-esp32:
	@echo "==> Flashing ESP32 Firmware via PlatformIO"
	cd $(ESP32_DIR) && pio run -t upload

clean:
	@echo "==> Cleaning up artifacts"
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf model_export/*.pkl
	rm -f nira_data_local.csv
