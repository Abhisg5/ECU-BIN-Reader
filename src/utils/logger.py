"""
Logging utilities for ECU BIN Reader
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Setup logging configuration for the application
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional log file path
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Default log file if none specified
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"ecu_bin_reader_{timestamp}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Suppress verbose logging from external libraries
    logging.getLogger('can').setLevel(logging.WARNING)
    logging.getLogger('cantools').setLevel(logging.WARNING)
    logging.getLogger('serial').setLevel(logging.WARNING)
    
    return root_logger


class LogHandler(logging.Handler):
    """Custom log handler for GUI integration"""
    
    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback
    
    def emit(self, record):
        if self.callback:
            log_entry = self.format(record)
            self.callback(log_entry)


def get_logger(name):
    """Get a logger instance with the given name"""
    return logging.getLogger(name) 