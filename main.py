#!/usr/bin/env python3
"""
ECU BIN Reader - Main Application Entry Point
Cross-platform desktop application for reading ECU BIN files via OBD2
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from src.gui.main_window import MainWindow
from src.utils.logger import setup_logging


def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting ECU BIN Reader application")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("ECU BIN Reader")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ECU Tools")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    logger.info("Application started successfully")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 