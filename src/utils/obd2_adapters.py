"""
OBD2 adapter detection and management utilities
"""

import serial
import serial.tools.list_ports
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class OBD2Adapter:
    """OBD2 adapter information"""
    port: str
    description: str
    manufacturer: str
    product_id: str
    vendor_id: str
    serial_number: str = ""
    is_connected: bool = False


class OBD2AdapterManager:
    """Manages OBD2 adapter detection and connection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.known_adapters = {
            # ELM327 variants
            "0403": "FTDI",  # FTDI chip
            "067b": "Prolific",  # Prolific chip
            "10c4": "Silicon Labs",  # CP210x
            "1a86": "QinHeng Electronics",  # CH340
            "2341": "Arduino",  # Arduino
            "04d8": "Microchip",  # Microchip
        }
    
    def scan_adapters(self) -> List[OBD2Adapter]:
        """
        Scan for available OBD2 adapters
        
        Returns:
            List of detected OBD2 adapters
        """
        adapters = []
        
        try:
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                # Check if this looks like an OBD2 adapter
                if self._is_obd2_adapter(port):
                    adapter = OBD2Adapter(
                        port=port.device,
                        description=port.description,
                        manufacturer=port.manufacturer or "Unknown",
                        product_id=port.pid or "",
                        vendor_id=port.vid or "",
                        serial_number=port.serial_number or ""
                    )
                    adapters.append(adapter)
                    self.logger.info(f"Found OBD2 adapter: {adapter.description} on {adapter.port}")
        
        except Exception as e:
            self.logger.error(f"Error scanning for OBD2 adapters: {e}")
        
        return adapters
    
    def _is_obd2_adapter(self, port) -> bool:
        """
        Check if a serial port is likely an OBD2 adapter
        
        Args:
            port: Serial port object
            
        Returns:
            True if likely OBD2 adapter
        """
        # Check for known OBD2 adapter descriptions
        obd2_keywords = [
            "elm327", "obd", "obd2", "diagnostic", "scanner",
            "bluetooth", "wifi", "usb", "serial"
        ]
        
        description = (port.description or "").lower()
        manufacturer = (port.manufacturer or "").lower()
        
        # Check for OBD2 keywords in description
        for keyword in obd2_keywords:
            if keyword in description or keyword in manufacturer:
                return True
        
        # Check for known vendor IDs
        if port.vid:
            vid_hex = f"{port.vid:04x}"
            if vid_hex in self.known_adapters:
                return True
        
        return False
    
    def test_adapter(self, adapter: OBD2Adapter) -> bool:
        """
        Test if an adapter is working
        
        Args:
            adapter: OBD2 adapter to test
            
        Returns:
            True if adapter responds correctly
        """
        try:
            with serial.Serial(adapter.port, 38400, timeout=2) as ser:
                # Send ATZ (reset) command
                ser.write(b"ATZ\r\n")
                response = ser.read(100).decode('ascii', errors='ignore')
                
                if "ELM327" in response or "OK" in response:
                    adapter.is_connected = True
                    self.logger.info(f"Adapter {adapter.port} is working")
                    return True
                else:
                    self.logger.warning(f"Adapter {adapter.port} did not respond correctly")
                    return False
        
        except Exception as e:
            self.logger.error(f"Error testing adapter {adapter.port}: {e}")
            return False
    
    def get_adapter_info(self, adapter: OBD2Adapter) -> Dict[str, str]:
        """
        Get detailed information about an adapter
        
        Args:
            adapter: OBD2 adapter
            
        Returns:
            Dictionary with adapter information
        """
        info = {
            "Port": adapter.port,
            "Description": adapter.description,
            "Manufacturer": adapter.manufacturer,
            "Product ID": adapter.product_id,
            "Vendor ID": adapter.vendor_id,
            "Serial Number": adapter.serial_number,
            "Connected": str(adapter.is_connected)
        }
        
        return info


def list_available_adapters() -> List[OBD2Adapter]:
    """
    Convenience function to list available OBD2 adapters
    
    Returns:
        List of available OBD2 adapters
    """
    manager = OBD2AdapterManager()
    return manager.scan_adapters() 