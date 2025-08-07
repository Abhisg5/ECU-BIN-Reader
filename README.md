# ECU BIN Reader

A cross-platform desktop application for reading BIN files from automotive ECUs via OBD2 interface.

## Features

- **Universal ECU Support**: Works with any ECU supporting OBD2 over CAN (ISO 15765-4), UDS (ISO 14229), or KWP2000 (ISO 14230)
- **Auto-Detection**: Dynamically detects ECU protocols and adjusts communication parameters
- **Security Access**: Modular seed/key solver for ECU security access
- **Cross-Platform**: Windows (.exe) and macOS (.app) support
- **Real-time Logging**: Live communication logs and progress tracking
- **Modular Design**: Plugin system for ECU definitions and protocols

## Requirements

- Python 3.8+
- OBD2 USB adapter (ELM327, STN1110, or similar)
- Vehicle with OBD2 support

## Installation

### From Source
```bash
git clone <repository>
cd ecu-bin-reader
pip install -r requirements.txt
python main.py
```

### Build Executables
```bash
# Windows
python build_windows.py

# macOS
python build_macos.py
```

## Usage

1. Connect OBD2 adapter to your computer
2. Launch the application
3. Select your OBD2 adapter from the dropdown
4. Click "Connect" to initialize communication
5. Click "Scan ECUs" to detect available ECUs
6. Click "Read BIN" to extract the ECU binary file
7. Save the BIN file with VIN and ECU ID

## Project Structure

```
ecu-bin-reader/
├── src/
│   ├── core/           # Core ECU communication logic
│   ├── gui/            # PyQt5 GUI components
│   ├── protocols/      # UDS, KWP, CAN protocols
│   ├── security/       # Security access modules
│   └── utils/          # Utility functions
├── profiles/           # ECU-specific profiles
├── plugins/            # Community plugin system
├── build/              # Build scripts and outputs
└── tests/              # Unit tests
```

## Supported Protocols

- **UDS (ISO 14229)**: Standard diagnostic protocol
- **KWP2000 (ISO 14230)**: Keyword Protocol 2000
- **ISO 15765-4**: CAN transport layer
- **ISO 11898**: CAN bus protocol

## Security Features

- Modular seed/key algorithms
- Automatic security access
- Retry mechanisms for failed operations
- Checksum verification

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Disclaimer

This tool is for educational and diagnostic purposes only. Always ensure compliance with local laws and vehicle warranty terms before use. 