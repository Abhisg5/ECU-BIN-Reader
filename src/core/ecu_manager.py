"""
ECU Manager - Main class for ECU communication and BIN extraction
"""

import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from src.protocols.uds import UDSProtocol
from src.protocols.kwp import KWPProtocol
from src.protocols.can_bus import CANBus
from src.security.security_access import SecurityAccess
from src.utils.obd2_adapters import OBD2Adapter


@dataclass
class ECUInfo:
    """ECU information"""
    ecu_id: str
    protocol: str  # "UDS", "KWP", "CAN"
    address: int
    vin: str = ""
    manufacturer: str = ""
    model: str = ""
    version: str = ""


@dataclass
class BINReadProgress:
    """BIN read progress information"""
    bytes_read: int
    total_bytes: int
    current_address: int
    status: str  # "reading", "complete", "error"
    error_message: str = ""


class ECUManger:
    """Main ECU management class"""
    
    def __init__(self, adapter: OBD2Adapter):
        self.adapter = adapter
        self.logger = logging.getLogger(__name__)
        self.can_bus = None
        self.uds_protocol = None
        self.kwp_protocol = None
        self.security_access = SecurityAccess()
        
        # ECU scanning results
        self.discovered_ecus: List[ECUInfo] = []
        self.selected_ecu: Optional[ECUInfo] = None
        
        # BIN read state
        self.bin_data = bytearray()
        self.read_progress = BINReadProgress(0, 0, 0, "idle")
        
    def initialize_communication(self) -> bool:
        """
        Initialize communication with the OBD2 adapter
        
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Initializing communication with adapter: {self.adapter.port}")
            
            # Initialize CAN bus
            self.can_bus = CANBus(self.adapter.port)
            if not self.can_bus.connect():
                self.logger.error("Failed to connect to CAN bus")
                return False
            
            # Initialize protocols
            self.uds_protocol = UDSProtocol(self.can_bus)
            self.kwp_protocol = KWPProtocol(self.can_bus)
            
            self.logger.info("Communication initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing communication: {e}")
            return False
    
    def scan_ecus(self) -> List[ECUInfo]:
        """
        Scan for available ECUs on the OBD2 network
        
        Returns:
            List of discovered ECUs
        """
        self.logger.info("Starting ECU scan...")
        self.discovered_ecus.clear()
        
        # Standard OBD2 ECU addresses (0x7E0-0x7EF)
        ecu_addresses = range(0x7E0, 0x7F0)
        
        for address in ecu_addresses:
            ecu_info = self._probe_ecu(address)
            if ecu_info:
                self.discovered_ecus.append(ecu_info)
                self.logger.info(f"Found ECU: {ecu_info.ecu_id} at 0x{address:03X}")
        
        self.logger.info(f"ECU scan complete. Found {len(self.discovered_ecus)} ECUs")
        return self.discovered_ecus
    
    def _probe_ecu(self, address: int) -> Optional[ECUInfo]:
        """
        Probe a specific ECU address for availability
        
        Args:
            address: ECU address to probe
            
        Returns:
            ECUInfo if ECU responds, None otherwise
        """
        try:
            # Try UDS protocol first
            if self.uds_protocol:
                response = self.uds_protocol.send_diagnostic_session_control(
                    address, 0x01  # Default session
                )
                if response and response.get('positive'):
                    return ECUInfo(
                        ecu_id=f"UDS_0x{address:03X}",
                        protocol="UDS",
                        address=address
                    )
            
            # Try KWP protocol
            if self.kwp_protocol:
                response = self.kwp_protocol.send_start_communication(address)
                if response and response.get('positive'):
                    return ECUInfo(
                        ecu_id=f"KWP_0x{address:03X}",
                        protocol="KWP",
                        address=address
                    )
            
            # Try direct CAN communication
            if self.can_bus:
                response = self.can_bus.send_raw_message(address, [0x01, 0x00])
                if response:
                    return ECUInfo(
                        ecu_id=f"CAN_0x{address:03X}",
                        protocol="CAN",
                        address=address
                    )
        
        except Exception as e:
            self.logger.debug(f"Error probing ECU at 0x{address:03X}: {e}")
        
        return None
    
    def select_ecu(self, ecu_info: ECUInfo) -> bool:
        """
        Select an ECU for communication
        
        Args:
            ecu_info: ECU to select
            
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Selecting ECU: {ecu_info.ecu_id}")
            self.selected_ecu = ecu_info
            
            # Get ECU information
            self._get_ecu_details(ecu_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error selecting ECU: {e}")
            return False
    
    def _get_ecu_details(self, ecu_info: ECUInfo):
        """Get detailed information about the ECU"""
        try:
            if ecu_info.protocol == "UDS" and self.uds_protocol:
                # Get VIN
                vin_response = self.uds_protocol.read_data_by_identifier(
                    ecu_info.address, 0xF190  # VIN identifier
                )
                if vin_response and vin_response.get('positive'):
                    ecu_info.vin = vin_response.get('data', '')
                
                # Get ECU identification
                ecu_id_response = self.uds_protocol.read_data_by_identifier(
                    ecu_info.address, 0xF187  # ECU identification
                )
                if ecu_id_response and ecu_id_response.get('positive'):
                    ecu_info.manufacturer = ecu_id_response.get('data', '')
        
        except Exception as e:
            self.logger.warning(f"Error getting ECU details: {e}")
    
    def read_bin_file(self, start_address: int = 0, end_address: int = None) -> bool:
        """
        Read BIN file from the selected ECU
        
        Args:
            start_address: Starting address for read
            end_address: Ending address for read (None for full ECU)
            
        Returns:
            True if successful
        """
        if not self.selected_ecu:
            self.logger.error("No ECU selected")
            return False
        
        try:
            self.logger.info(f"Starting BIN read from ECU: {self.selected_ecu.ecu_id}")
            
            # Initialize progress
            if end_address is None:
                end_address = 0x100000  # Default 1MB
            
            self.read_progress = BINReadProgress(
                bytes_read=0,
                total_bytes=end_address - start_address,
                current_address=start_address,
                status="reading"
            )
            
            # Perform security access if needed
            if not self._perform_security_access():
                self.logger.error("Security access failed")
                return False
            
            # Read BIN data
            self.bin_data = bytearray()
            current_address = start_address
            
            while current_address < end_address:
                # Read memory block
                block_data = self._read_memory_block(current_address)
                if block_data is None:
                    self.logger.error(f"Failed to read memory at 0x{current_address:08X}")
                    break
                
                self.bin_data.extend(block_data)
                current_address += len(block_data)
                
                # Update progress
                self.read_progress.bytes_read = len(self.bin_data)
                self.read_progress.current_address = current_address
                
                # Small delay to avoid overwhelming the ECU
                time.sleep(0.01)
            
            self.read_progress.status = "complete"
            self.logger.info(f"BIN read complete. Size: {len(self.bin_data)} bytes")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reading BIN file: {e}")
            self.read_progress.status = "error"
            self.read_progress.error_message = str(e)
            return False
    
    def _perform_security_access(self) -> bool:
        """Perform security access on the ECU"""
        try:
            if self.selected_ecu.protocol == "UDS" and self.uds_protocol:
                return self.security_access.perform_uds_security_access(
                    self.uds_protocol, self.selected_ecu.address
                )
            elif self.selected_ecu.protocol == "KWP" and self.kwp_protocol:
                return self.security_access.perform_kwp_security_access(
                    self.kwp_protocol, self.selected_ecu.address
                )
            
            return True  # Assume no security needed for direct CAN
            
        except Exception as e:
            self.logger.error(f"Error performing security access: {e}")
            return False
    
    def _read_memory_block(self, address: int, block_size: int = 256) -> Optional[bytes]:
        """Read a block of memory from the ECU"""
        try:
            if self.selected_ecu.protocol == "UDS" and self.uds_protocol:
                return self.uds_protocol.read_memory_by_address(
                    self.selected_ecu.address, address, block_size
                )
            elif self.selected_ecu.protocol == "KWP" and self.kwp_protocol:
                return self.kwp_protocol.read_memory_by_address(
                    self.selected_ecu.address, address, block_size
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading memory block at 0x{address:08X}: {e}")
            return None
    
    def save_bin_file(self, filename: str = None) -> bool:
        """
        Save the read BIN data to a file
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            True if successful
        """
        try:
            if not self.bin_data:
                self.logger.error("No BIN data to save")
                return False
            
            if filename is None:
                # Generate filename with VIN and ECU ID
                vin = self.selected_ecu.vin or "UNKNOWN"
                ecu_id = self.selected_ecu.ecu_id.replace(" ", "_")
                filename = f"{vin}_{ecu_id}.bin"
            
            # Ensure output directory exists
            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write BIN file
            with open(output_path, 'wb') as f:
                f.write(self.bin_data)
            
            self.logger.info(f"BIN file saved: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving BIN file: {e}")
            return False
    
    def get_progress(self) -> BINReadProgress:
        """Get current read progress"""
        return self.read_progress
    
    def disconnect(self):
        """Disconnect from the ECU and adapter"""
        try:
            if self.can_bus:
                self.can_bus.disconnect()
            
            self.logger.info("Disconnected from ECU")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}") 