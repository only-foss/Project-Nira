# Contributing to Project Nira

Thank you for helping make water quality monitoring accessible to everyone!

## Quick Start

```bash
git clone https://github.com/only-foss/Project-Nira.git
cd Project-Nira

# Firmware
pip install platformio
pio run                    # build
pio run --target upload    # flash
pio device monitor         # serial monitor

# GUI
pip install -r requirements.txt
python software/nira_gui.py
```

## How to Contribute

1. Check [Issues](https://github.com/only-foss/Project-Nira/issues) for open tasks
2. Fork the repo, create a branch: `git checkout -b feat/your-feature`
3. Make changes following the code style in `.cursorrules`
4. Add/update tests in `tests/`
5. Update relevant docs (see `.cursorrules` § Documentation Auto-Update Rules)
6. Commit using the format in `.cursorrules` § Commit Message Format
7. Open a Pull Request

## Code Style

- Firmware (C++): see `.cursorrules` § Firmware Rules
- GUI (Python): PEP 8, Google docstrings, type hints
- All code must pass the FOSS compliance checklist in `.cursorrules`

## License

By contributing, you agree your code will be released under:
- Firmware/Software: MIT
- Hardware: CERN-OHL-P-2.0
- Docs: CC-BY-SA-4.0
