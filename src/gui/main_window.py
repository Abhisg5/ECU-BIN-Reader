"""
Main GUI window for ECU BIN Reader
"""

import sys
import logging
from typing import Optional, List
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QComboBox, QTextEdit, QProgressBar, QLabel,
    QGroupBox, QTabWidget, QFileDialog, QMessageBox, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QSpinBox, QLineEdit, QFormLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

from src.core.ecu_manager import ECUManger, ECUInfo, BINReadProgress
from src.utils.obd2_adapters import OBD2Adapter, list_available_adapters
from src.utils.logger import LogHandler


class BINReadWorker(QThread):
    """Worker thread for BIN reading operations"""
    
    progress_updated = pyqtSignal(object)  # BINReadProgress
    log_message = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, ecu_manager: ECUManger, start_address: int = 0, end_address: int = None):
        super().__init__()
        self.ecu_manager = ecu_manager
        self.start_address = start_address
        self.end_address = end_address
        self.logger = logging.getLogger(__name__)
        
        # Setup log handler for GUI
        log_handler = LogHandler(self.log_message.emit)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(log_handler)
    
    def run(self):
        """Run the BIN read operation"""
        try:
            self.log_message.emit("Starting BIN read operation...")
            
            # Read BIN file
            success = self.ecu_manager.read_bin_file(self.start_address, self.end_address)
            
            if success:
                self.log_message.emit("BIN read completed successfully")
                self.finished.emit(True, "BIN read completed successfully")
            else:
                self.log_message.emit("BIN read failed")
                self.finished.emit(False, "BIN read failed")
                
        except Exception as e:
            self.log_message.emit(f"Error during BIN read: {e}")
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.ecu_manager: Optional[ECUManger] = None
        self.selected_adapter: Optional[OBD2Adapter] = None
        self.discovered_ecus: List[ECUInfo] = []
        self.selected_ecu: Optional[ECUInfo] = None
        self.bin_read_worker: Optional[BINReadWorker] = None
        
        # Setup UI
        self.setup_ui()
        self.setup_logging()
        
        # Start periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.start(100)  # Update every 100ms
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("ECU BIN Reader v1.0 - Professional ECU Diagnostic Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(700, 500)
        self.resize(1200, 800)
        
        # Set application icon and style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 1.5ex;
                padding-top: 15px;
                padding-bottom: 15px;
                padding-left: 12px;
                padding-right: 12px;
                background-color: #34495e;
                color: #ecf0f1;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #3498db;
                font-weight: bold;
                font-size: 12px;
                background-color: #34495e;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                color: white;
                padding: 4px 8px;
                border-radius: 6px;
                font-weight: bold;
                min-height: 24px;
                font-size: 9px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border: 1px solid #21618c;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
            QComboBox {
                border: 2px solid #34495e;
                border-radius: 6px;
                padding: 4px;
                background-color: #34495e;
                color: #ecf0f1;
                min-height: 24px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ecf0f1;
            }
            QProgressBar {
                border: 2px solid #34495e;
                border-radius: 6px;
                text-align: center;
                background-color: #2c3e50;
                color: #ecf0f1;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 4px;
            }
            QTextEdit {
                border: 2px solid #34495e;
                border-radius: 6px;
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 8px;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                font-size: 11px;
            }
            QTableWidget {
                border: 2px solid #34495e;
                border-radius: 6px;
                background-color: #2c3e50;
                color: #ecf0f1;
                gridline-color: #34495e;
                alternate-background-color: #34495e;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 8px;
                border: none;
                font-weight: bold;
                border-bottom: 1px solid #2c3e50;
            }
            QTabWidget::pane {
                border: 2px solid #34495e;
                border-radius: 6px;
                background-color: #2c3e50;
            }
            QTabBar::tab {
                background-color: #34495e;
                border: 2px solid #34495e;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 10px 20px;
                margin-right: 2px;
                color: #ecf0f1;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #2c3e50;
                border-bottom: 2px solid #2c3e50;
                color: #3498db;
            }
            QTabBar::tab:hover {
                background-color: #3a4a5a;
            }
            QLabel {
                color: #ecf0f1;
                background-color: transparent;
            }
            QSpinBox {
                border: 2px solid #34495e;
                border-radius: 6px;
                padding: 8px;
                background-color: #34495e;
                color: #ecf0f1;
                min-height: 25px;
            }
            QSpinBox:focus {
                border-color: #3498db;
            }
            QCheckBox {
                color: #ecf0f1;
                spacing: 10px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #34495e;
                border-radius: 4px;
                background-color: #2c3e50;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #3498db;
                border-radius: 4px;
                background-color: #3498db;
            }
            QFormLayout {
                color: #ecf0f1;
            }
            QVBoxLayout, QHBoxLayout {
                background-color: transparent;
            }
            QSplitter::handle {
                background-color: #34495e;
                border: 1px solid #2c3e50;
            }
            QMenuBar {
                background-color: #34495e;
                color: #ecf0f1;
                border: none;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
            }
            QMenuBar::item:selected {
                background-color: #3498db;
            }
            QMenu {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout with proper margins
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)  # Prevent panels from collapsing
        main_layout.addWidget(splitter)
        
        # Left panel - Controls (responsive width)
        left_panel = self.create_control_panel()
        left_panel.setMinimumWidth(300)
        left_panel.setMaximumWidth(800)
        splitter.addWidget(left_panel)
        
        # Right panel - Logs and Progress (expandable)
        right_panel = self.create_log_panel()
        right_panel.setMinimumWidth(300)
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (40% left, 60% right)
        splitter.setSizes([400, 600])
        
        # Setup menu bar
        self.setup_menu_bar()
    
    def create_control_panel(self) -> QWidget:
        """Create the control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title and status
        title_label = QLabel("ECU BIN Reader")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #3498db;
            padding: 15px;
            background-color: #1a252f;
            border: 2px solid #3498db;
            border-radius: 10px;
            margin-bottom: 15px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Status indicator
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #27ae60;
            padding: 8px;
            background-color: #1a252f;
            border: 2px solid #27ae60;
            border-radius: 6px;
            margin-bottom: 10px;
            font-weight: bold;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Adapter Selection
        adapter_group = QGroupBox("🔌 OBD2 Adapter")
        adapter_layout = QVBoxLayout(adapter_group)
        adapter_layout.setSpacing(6)
        adapter_layout.setContentsMargins(6, 10, 6, 6)
        
        self.adapter_combo = QComboBox()
        self.adapter_combo.setMinimumHeight(24)
        self.adapter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.adapter_combo.addItem("No adapters detected")
        adapter_layout.addWidget(self.adapter_combo)
        
        adapter_buttons_layout = QHBoxLayout()
        adapter_buttons_layout.setSpacing(6)
        adapter_buttons_layout.setContentsMargins(0, 5, 0, 0)
        
        self.scan_adapters_btn = QPushButton("🔍 Scan")
        self.scan_adapters_btn.clicked.connect(self.scan_adapters)
        self.scan_adapters_btn.setMinimumHeight(24)
        self.scan_adapters_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        adapter_buttons_layout.addWidget(self.scan_adapters_btn)
        
        self.connect_btn = QPushButton("🔗 Connect")
        self.connect_btn.clicked.connect(self.connect_adapter)
        self.connect_btn.setEnabled(False)
        self.connect_btn.setMinimumHeight(24)
        self.connect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        adapter_buttons_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("❌ Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_adapter)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setMinimumHeight(24)
        self.disconnect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        adapter_buttons_layout.addWidget(self.disconnect_btn)
        
        adapter_layout.addLayout(adapter_buttons_layout)
        layout.addWidget(adapter_group)
        
        # ECU Selection
        ecu_group = QGroupBox("🚗 ECU Selection")
        ecu_layout = QVBoxLayout(ecu_group)
        ecu_layout.setSpacing(6)
        ecu_layout.setContentsMargins(6, 10, 6, 6)
        
        self.ecu_combo = QComboBox()
        self.ecu_combo.setMinimumHeight(24)
        self.ecu_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ecu_combo.addItem("No ECUs detected")
        self.ecu_combo.currentIndexChanged.connect(self.on_ecu_selected)
        ecu_layout.addWidget(self.ecu_combo)
        
        ecu_buttons_layout = QHBoxLayout()
        ecu_buttons_layout.setSpacing(6)
        ecu_buttons_layout.setContentsMargins(0, 5, 0, 0)
        
        self.scan_ecus_btn = QPushButton("🔍 Scan")
        self.scan_ecus_btn.clicked.connect(self.scan_ecus)
        self.scan_ecus_btn.setEnabled(False)
        self.scan_ecus_btn.setMinimumHeight(24)
        self.scan_ecus_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ecu_buttons_layout.addWidget(self.scan_ecus_btn)
        
        self.select_ecu_btn = QPushButton("✅ Select")
        self.select_ecu_btn.clicked.connect(self.select_ecu)
        self.select_ecu_btn.setEnabled(False)
        self.select_ecu_btn.setMinimumHeight(24)
        self.select_ecu_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ecu_buttons_layout.addWidget(self.select_ecu_btn)
        
        ecu_layout.addLayout(ecu_buttons_layout)
        layout.addWidget(ecu_group)
        
        # ECU Information
        self.ecu_info_group = QGroupBox("ECU Information")
        ecu_info_layout = QFormLayout(self.ecu_info_group)
        
        self.ecu_id_label = QLabel("Not selected")
        ecu_info_layout.addRow("ECU ID:", self.ecu_id_label)
        
        self.ecu_protocol_label = QLabel("Not selected")
        ecu_info_layout.addRow("Protocol:", self.ecu_protocol_label)
        
        self.ecu_address_label = QLabel("Not selected")
        ecu_info_layout.addRow("Address:", self.ecu_address_label)
        
        self.ecu_vin_label = QLabel("Not selected")
        ecu_info_layout.addRow("VIN:", self.ecu_vin_label)
        
        layout.addWidget(self.ecu_info_group)
        
        # BIN Read Settings
        bin_group = QGroupBox("BIN Read Settings")
        bin_layout = QFormLayout(bin_group)
        
        self.start_address_spin = QSpinBox()
        self.start_address_spin.setRange(0, 0xFFFFFF)
        self.start_address_spin.setPrefix("0x")
        self.start_address_spin.setDisplayIntegerBase(16)
        bin_layout.addRow("Start Address:", self.start_address_spin)
        
        self.end_address_spin = QSpinBox()
        self.end_address_spin.setRange(0, 0xFFFFFF)
        self.end_address_spin.setValue(0x100000)  # Default 1MB
        self.end_address_spin.setPrefix("0x")
        self.end_address_spin.setDisplayIntegerBase(16)
        bin_layout.addRow("End Address:", self.end_address_spin)
        
        self.block_size_spin = QSpinBox()
        self.block_size_spin.setRange(1, 4096)
        self.block_size_spin.setValue(256)
        bin_layout.addRow("Block Size:", self.block_size_spin)
        
        layout.addWidget(bin_group)
        
        # BIN Read Controls
        read_group = QGroupBox("💾 BIN Read Controls")
        read_layout = QVBoxLayout(read_group)
        read_layout.setSpacing(6)
        read_layout.setContentsMargins(6, 10, 6, 6)
        
        self.read_bin_btn = QPushButton("📖 Read BIN")
        self.read_bin_btn.clicked.connect(self.read_bin)
        self.read_bin_btn.setEnabled(False)
        self.read_bin_btn.setMinimumHeight(28)
        self.read_bin_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.read_bin_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        read_layout.addWidget(self.read_bin_btn)
        
        self.save_bin_btn = QPushButton("💾 Save BIN")
        self.save_bin_btn.clicked.connect(self.save_bin)
        self.save_bin_btn.setEnabled(False)
        self.save_bin_btn.setMinimumHeight(28)
        self.save_bin_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_bin_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        read_layout.addWidget(self.save_bin_btn)
        
        layout.addWidget(read_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return panel
    
    def create_log_panel(self) -> QWidget:
        """Create the log panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Communication Log
        comm_group = QGroupBox("Communication Log")
        comm_layout = QVBoxLayout(comm_group)
        
        self.comm_log = QTextEdit()
        self.comm_log.setReadOnly(True)
        self.comm_log.setFont(QFont("Courier", 9))
        comm_layout.addWidget(self.comm_log)
        
        comm_buttons_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        comm_buttons_layout.addWidget(self.clear_log_btn)
        
        self.save_log_btn = QPushButton("Save Log")
        self.save_log_btn.clicked.connect(self.save_log)
        comm_buttons_layout.addWidget(self.save_log_btn)
        
        comm_layout.addLayout(comm_buttons_layout)
        tab_widget.addTab(comm_group, "Communication")
        
        # ECU Discovery
        discovery_group = QGroupBox("ECU Discovery")
        discovery_layout = QVBoxLayout(discovery_group)
        
        self.ecu_table = QTableWidget()
        self.ecu_table.setColumnCount(5)
        self.ecu_table.setHorizontalHeaderLabels(["ECU ID", "Protocol", "Address", "VIN", "Manufacturer"])
        self.ecu_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        discovery_layout.addWidget(self.ecu_table)
        
        tab_widget.addTab(discovery_group, "ECU Discovery")
        
        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.currentTextChanged.connect(self.change_log_level)
        settings_layout.addRow("Log Level:", self.log_level_combo)
        
        self.auto_save_check = QCheckBox("Auto-save BIN after read")
        self.auto_save_check.setChecked(True)
        settings_layout.addRow("", self.auto_save_check)
        
        tab_widget.addTab(settings_group, "Settings")
        
        return panel
    
    def setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        save_bin_action = file_menu.addAction('Save BIN...')
        save_bin_action.triggered.connect(self.save_bin)
        
        save_log_action = file_menu.addAction('Save Log...')
        save_log_action.triggered.connect(self.save_log)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        scan_adapters_action = tools_menu.addAction('Scan Adapters')
        scan_adapters_action.triggered.connect(self.scan_adapters)
        
        scan_ecus_action = tools_menu.addAction('Scan ECUs')
        scan_ecus_action.triggered.connect(self.scan_ecus)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
    
    def setup_logging(self):
        """Setup logging for GUI"""
        # Add GUI log handler
        log_handler = LogHandler(self.add_log_message)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)
    
    def scan_adapters(self):
        """Scan for available OBD2 adapters"""
        try:
            self.update_status("Scanning for OBD2 adapters...")
            self.log_message("🔍 Scanning for OBD2 adapters...")
            
            adapters = list_available_adapters()
            
            self.adapter_combo.clear()
            self.adapter_combo.addItem("No adapters detected")
            
            for adapter in adapters:
                self.adapter_combo.addItem(f"{adapter.description} ({adapter.port})", adapter)
            
            if adapters:
                self.connect_btn.setEnabled(True)
                self.disconnect_btn.setEnabled(False)
                self.log_message(f"✅ Found {len(adapters)} OBD2 adapter(s)")
                self.update_status(f"Found {len(adapters)} OBD2 adapter(s)")
            else:
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(False)
                self.log_message("⚠️ No OBD2 adapters found")
                self.update_status("No OBD2 adapters found")
                
        except Exception as e:
            self.log_message(f"❌ Error scanning adapters: {e}")
            self.update_status("Error scanning adapters")
    
    def connect_adapter(self):
        """Connect to the selected OBD2 adapter"""
        try:
            if self.adapter_combo.currentIndex() < 0:
                QMessageBox.warning(self, "No Adapter", "Please select an OBD2 adapter")
                return
            
            adapter = self.adapter_combo.currentData()
            self.selected_adapter = adapter
            
            self.log_message(f"Connecting to adapter: {adapter.description}")
            
            # Create ECU manager
            self.ecu_manager = ECUManger(adapter)
            
            # Initialize communication
            if self.ecu_manager.initialize_communication():
                self.log_message("Successfully connected to OBD2 adapter")
                self.scan_ecus_btn.setEnabled(True)
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)
            else:
                self.log_message("Failed to connect to OBD2 adapter")
                QMessageBox.critical(self, "Connection Error", "Failed to connect to OBD2 adapter")
                
        except Exception as e:
            self.log_message(f"Error connecting to adapter: {e}")
            QMessageBox.critical(self, "Connection Error", f"Error connecting to adapter: {e}")
    
    def disconnect_adapter(self):
        """Disconnect from the OBD2 adapter"""
        try:
            if self.ecu_manager:
                self.ecu_manager.disconnect()
                self.ecu_manager = None
            
            self.selected_adapter = None
            self.discovered_ecus.clear()
            self.selected_ecu = None
            
            self.log_message("Disconnected from OBD2 adapter")
            
            # Reset UI
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.scan_ecus_btn.setEnabled(False)
            self.select_ecu_btn.setEnabled(False)
            self.read_bin_btn.setEnabled(False)
            self.save_bin_btn.setEnabled(False)
            
            self.update_ecu_info()
            self.update_ecu_table()
            
        except Exception as e:
            self.log_message(f"Error disconnecting: {e}")
    
    def scan_ecus(self):
        """Scan for available ECUs"""
        try:
            if not self.ecu_manager:
                QMessageBox.warning(self, "No Connection", "Please connect to an OBD2 adapter first")
                return
            
            self.log_message("Scanning for ECUs...")
            
            self.discovered_ecus = self.ecu_manager.scan_ecus()
            
            self.update_ecu_table()
            
            if self.discovered_ecus:
                self.ecu_combo.clear()
                for ecu in self.discovered_ecus:
                    self.ecu_combo.addItem(f"{ecu.ecu_id} ({ecu.protocol})", ecu)
                
                self.select_ecu_btn.setEnabled(True)
                self.log_message(f"Found {len(self.discovered_ecus)} ECU(s)")
            else:
                self.select_ecu_btn.setEnabled(False)
                self.log_message("No ECUs found")
                
        except Exception as e:
            self.log_message(f"Error scanning ECUs: {e}")
            QMessageBox.critical(self, "Scan Error", f"Error scanning ECUs: {e}")
    
    def on_ecu_selected(self, index):
        """Handle ECU selection from combo box"""
        if index >= 0:
            ecu = self.ecu_combo.currentData()
            self.selected_ecu = ecu
            self.update_ecu_info()
    
    def select_ecu(self):
        """Select the current ECU"""
        try:
            if self.ecu_combo.currentIndex() < 0:
                QMessageBox.warning(self, "No ECU", "Please select an ECU first")
                return
            
            ecu = self.ecu_combo.currentData()
            
            if self.ecu_manager.select_ecu(ecu):
                self.selected_ecu = ecu
                self.update_ecu_info()
                self.read_bin_btn.setEnabled(True)
                self.log_message(f"Selected ECU: {ecu.ecu_id}")
            else:
                self.log_message(f"Failed to select ECU: {ecu.ecu_id}")
                QMessageBox.warning(self, "Selection Error", f"Failed to select ECU: {ecu.ecu_id}")
                
        except Exception as e:
            self.log_message(f"Error selecting ECU: {e}")
            QMessageBox.critical(self, "Selection Error", f"Error selecting ECU: {e}")
    
    def read_bin(self):
        """Start BIN read operation"""
        try:
            if not self.selected_ecu:
                QMessageBox.warning(self, "No ECU", "Please select an ECU first")
                return
            
            # Get read parameters
            start_address = self.start_address_spin.value()
            end_address = self.end_address_spin.value()
            
            if start_address >= end_address:
                QMessageBox.warning(self, "Invalid Range", "Start address must be less than end address")
                return
            
            # Disable controls during read
            self.read_bin_btn.setEnabled(False)
            self.read_bin_btn.setText("Reading...")
            
            # Start worker thread
            self.bin_read_worker = BINReadWorker(self.ecu_manager, start_address, end_address)
            self.bin_read_worker.progress_updated.connect(self.update_progress)
            self.bin_read_worker.log_message.connect(self.log_message)
            self.bin_read_worker.finished.connect(self.on_bin_read_finished)
            self.bin_read_worker.start()
            
            self.log_message("Started BIN read operation")
            
        except Exception as e:
            self.log_message(f"Error starting BIN read: {e}")
            QMessageBox.critical(self, "Read Error", f"Error starting BIN read: {e}")
    
    def on_bin_read_finished(self, success: bool, message: str):
        """Handle BIN read completion"""
        self.read_bin_btn.setEnabled(True)
        self.read_bin_btn.setText("Read BIN")
        
        if success:
            self.save_bin_btn.setEnabled(True)
            self.log_message("BIN read completed successfully")
            
            if self.auto_save_check.isChecked():
                self.save_bin()
        else:
            self.log_message(f"BIN read failed: {message}")
            QMessageBox.warning(self, "Read Error", f"BIN read failed: {message}")
    
    def save_bin(self):
        """Save the BIN file"""
        try:
            if not self.ecu_manager or not self.ecu_manager.bin_data:
                QMessageBox.warning(self, "No Data", "No BIN data to save")
                return
            
            # Generate default filename
            if self.selected_ecu:
                vin = self.selected_ecu.vin or "UNKNOWN"
                ecu_id = self.selected_ecu.ecu_id.replace(" ", "_")
                default_filename = f"{vin}_{ecu_id}.bin"
            else:
                default_filename = "ecu_dump.bin"
            
            # Show file dialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save BIN File", default_filename, "BIN Files (*.bin);;All Files (*)"
            )
            
            if filename:
                if self.ecu_manager.save_bin_file(filename):
                    self.log_message(f"BIN file saved: {filename}")
                    QMessageBox.information(self, "Success", f"BIN file saved successfully:\n{filename}")
                else:
                    self.log_message("Failed to save BIN file")
                    QMessageBox.critical(self, "Save Error", "Failed to save BIN file")
                    
        except Exception as e:
            self.log_message(f"Error saving BIN file: {e}")
            QMessageBox.critical(self, "Save Error", f"Error saving BIN file: {e}")
    
    def update_progress(self):
        """Update progress display"""
        if self.ecu_manager:
            progress = self.ecu_manager.get_progress()
            
            if progress.status == "reading":
                if progress.total_bytes > 0:
                    percent = (progress.bytes_read / progress.total_bytes) * 100
                    self.progress_bar.setValue(int(percent))
                    self.progress_label.setText(
                        f"📖 Reading: {progress.bytes_read:,} / {progress.total_bytes:,} bytes "
                        f"(0x{progress.current_address:08X})"
                    )
                    self.update_status("Reading ECU memory...")
            elif progress.status == "complete":
                self.progress_bar.setValue(100)
                self.progress_label.setText("✅ Complete")
                self.update_status("BIN read completed successfully")
            elif progress.status == "error":
                self.progress_bar.setValue(0)
                self.progress_label.setText(f"❌ Error: {progress.error_message}")
                self.update_status("Error occurred during read")
    
    def update_status(self, message: str):
        """Update the status label"""
        self.status_label.setText(f"Status: {message}")
        if "Error" in message:
            self.status_label.setStyleSheet("""
                font-size: 12px;
                color: #e74c3c;
                padding: 8px;
                background-color: #1a252f;
                border: 2px solid #e74c3c;
                border-radius: 6px;
                margin-bottom: 10px;
                font-weight: bold;
            """)
        elif "Complete" in message or "Success" in message:
            self.status_label.setStyleSheet("""
                font-size: 12px;
                color: #27ae60;
                padding: 8px;
                background-color: #1a252f;
                border: 2px solid #27ae60;
                border-radius: 6px;
                margin-bottom: 10px;
                font-weight: bold;
            """)
        else:
            self.status_label.setStyleSheet("""
                font-size: 12px;
                color: #3498db;
                padding: 8px;
                background-color: #1a252f;
                border: 2px solid #3498db;
                border-radius: 6px;
                margin-bottom: 10px;
                font-weight: bold;
            """)
    
    def update_ecu_info(self):
        """Update ECU information display"""
        if self.selected_ecu:
            self.ecu_id_label.setText(self.selected_ecu.ecu_id)
            self.ecu_protocol_label.setText(self.selected_ecu.protocol)
            self.ecu_address_label.setText(f"0x{self.selected_ecu.address:03X}")
            self.ecu_vin_label.setText(self.selected_ecu.vin or "Unknown")
        else:
            self.ecu_id_label.setText("Not selected")
            self.ecu_protocol_label.setText("Not selected")
            self.ecu_address_label.setText("Not selected")
            self.ecu_vin_label.setText("Not selected")
    
    def update_ecu_table(self):
        """Update ECU discovery table"""
        self.ecu_table.setRowCount(len(self.discovered_ecus))
        
        for row, ecu in enumerate(self.discovered_ecus):
            self.ecu_table.setItem(row, 0, QTableWidgetItem(ecu.ecu_id))
            self.ecu_table.setItem(row, 1, QTableWidgetItem(ecu.protocol))
            self.ecu_table.setItem(row, 2, QTableWidgetItem(f"0x{ecu.address:03X}"))
            self.ecu_table.setItem(row, 3, QTableWidgetItem(ecu.vin or ""))
            self.ecu_table.setItem(row, 4, QTableWidgetItem(ecu.manufacturer or ""))
    
    def add_log_message(self, message: str):
        """Add a message to the log"""
        self.comm_log.append(message)
        
        # Auto-scroll to bottom
        scrollbar = self.comm_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def log_message(self, message: str):
        """Log a message (alias for add_log_message)"""
        self.add_log_message(message)
    
    def clear_log(self):
        """Clear the communication log"""
        self.comm_log.clear()
    
    def save_log(self):
        """Save the communication log"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Log File", "ecu_bin_reader.log", "Log Files (*.log);;Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(self.comm_log.toPlainText())
                
                self.log_message(f"Log saved: {filename}")
                QMessageBox.information(self, "Success", f"Log saved successfully:\n{filename}")
                
        except Exception as e:
            self.log_message(f"Error saving log: {e}")
            QMessageBox.critical(self, "Save Error", f"Error saving log: {e}")
    
    def change_log_level(self, level: str):
        """Change the log level"""
        try:
            import logging
            numeric_level = getattr(logging, level.upper(), None)
            if numeric_level is not None:
                logging.getLogger().setLevel(numeric_level)
                self.log_message(f"Log level changed to: {level}")
        except Exception as e:
            self.log_message(f"Error changing log level: {e}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About ECU BIN Reader",
            "ECU BIN Reader v1.0\n\n"
            "Cross-platform ECU diagnostic and BIN extraction tool\n\n"
            "Supports UDS, KWP, and CAN protocols\n"
            "Universal ECU support with modular design\n\n"
            "For educational and diagnostic purposes only"
        )
    
    def closeEvent(self, event):
        """Handle application close event"""
        try:
            if self.ecu_manager:
                self.ecu_manager.disconnect()
            
            if self.bin_read_worker and self.bin_read_worker.isRunning():
                self.bin_read_worker.terminate()
                self.bin_read_worker.wait()
            
            event.accept()
            
        except Exception as e:
            self.log_message(f"Error during shutdown: {e}")
            event.accept() 