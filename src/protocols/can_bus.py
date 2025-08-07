"""
CAN Bus communication module for OBD2 interface
"""

import can
import logging
import time
from typing import Optional, List, Dict
from src.utils.obd2_adapters import OBD2Adapter


class CANBus:
    """CAN Bus communication class"""
    
    def __init__(self, adapter: OBD2Adapter):
        self.adapter = adapter
        self.logger = logging.getLogger(__name__)
        self.bus = None
        self.is_connected = False
        
        # CAN configuration
        self.bitrate = 500000  # 500 kbps
        self.channel = None
        
    def connect(self) -> bool:
        """
        Connect to the CAN bus via OBD2 adapter
        
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Connecting to CAN bus via {self.adapter.port}")
            
            # Try different CAN interfaces
            interfaces = [
                ('socketcan', 'can0'),
                ('pcan', 'PCAN_USBBUS1'),
                ('ixxat', '0'),
                ('vector', '0'),
                ('kvaser', '0'),
                ('serial', self.adapter.port),  # Serial CAN adapter
            ]
            
            for interface_type, channel in interfaces:
                try:
                    self.bus = can.interface.Bus(
                        channel=channel,
                        bustype=interface_type,
                        bitrate=self.bitrate
                    )
                    self.channel = channel
                    self.is_connected = True
                    self.logger.info(f"Connected to CAN bus via {interface_type}:{channel}")
                    return True
                    
                except Exception as e:
                    self.logger.debug(f"Failed to connect via {interface_type}:{channel} - {e}")
                    continue
            
            # If no standard interface works, try serial CAN
            if not self.is_connected:
                return self._connect_serial_can()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error connecting to CAN bus: {e}")
            return False
    
    def _connect_serial_can(self) -> bool:
        """Connect via serial CAN adapter (ELM327, etc.)"""
        try:
            import serial
            
            # Configure serial connection
            ser = serial.Serial(
                port=self.adapter.port,
                baudrate=38400,
                timeout=1
            )
            
            # Test ELM327 commands
            commands = [
                b"ATZ\r\n",      # Reset
                b"ATE0\r\n",      # Echo off
                b"ATL0\r\n",      # Linefeeds off
                b"ATS0\r\n",      # Spaces off
                b"ATH0\r\n",      # Headers off
                b"ATSP0\r\n",     # Auto protocol
            ]
            
            for cmd in commands:
                ser.write(cmd)
                response = ser.read(100).decode('ascii', errors='ignore')
                if "OK" not in response and "ELM327" not in response:
                    self.logger.warning(f"Unexpected response to {cmd}: {response}")
            
            ser.close()
            
            # Create a custom CAN interface for serial
            self.bus = SerialCANInterface(self.adapter.port)
            self.is_connected = True
            self.logger.info("Connected via serial CAN adapter")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting via serial CAN: {e}")
            return False
    
    def send_message(self, arbitration_id: int, data: List[int], extended: bool = False) -> bool:
        """
        Send a CAN message
        
        Args:
            arbitration_id: CAN ID
            data: Message data bytes
            extended: Use extended frame format
            
        Returns:
            True if successful
        """
        try:
            if not self.is_connected or not self.bus:
                self.logger.error("CAN bus not connected")
                return False
            
            message = can.Message(
                arbitration_id=arbitration_id,
                data=data,
                is_extended_id=extended
            )
            
            self.bus.send(message)
            self.logger.debug(f"Sent CAN message: ID=0x{arbitration_id:03X}, Data={data}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending CAN message: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[can.Message]:
        """
        Receive a CAN message
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            CAN message or None
        """
        try:
            if not self.is_connected or not self.bus:
                return None
            
            message = self.bus.recv(timeout=timeout)
            if message:
                self.logger.debug(f"Received CAN message: ID=0x{message.arbitration_id:03X}, Data={list(message.data)}")
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error receiving CAN message: {e}")
            return None
    
    def send_raw_message(self, address: int, data: List[int]) -> Optional[List[int]]:
        """
        Send a raw message and wait for response
        
        Args:
            address: Target address
            data: Message data
            
        Returns:
            Response data or None
        """
        try:
            # Send message
            if not self.send_message(address, data):
                return None
            
            # Wait for response
            response = self.receive_message(timeout=2.0)
            if response:
                return list(response.data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in send_raw_message: {e}")
            return None
    
    def disconnect(self):
        """Disconnect from CAN bus"""
        try:
            if self.bus:
                self.bus.shutdown()
                self.bus = None
            
            self.is_connected = False
            self.logger.info("Disconnected from CAN bus")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from CAN bus: {e}")


class SerialCANInterface:
    """Custom CAN interface for serial adapters"""
    
    def __init__(self, port: str):
        self.port = port
        self.serial = None
        self.logger = logging.getLogger(__name__)
    
    def send(self, message: can.Message):
        """Send a CAN message via serial"""
        try:
            if not self.serial:
                import serial
                self.serial = serial.Serial(
                    port=self.port,
                    baudrate=38400,
                    timeout=1
                )
            
            # Convert CAN message to serial format
            can_id = f"{message.arbitration_id:03X}"
            data = ''.join(f"{b:02X}" for b in message.data)
            
            # ELM327 format: "t" + ID + data length + data
            cmd = f"t{can_id}{len(message.data):01X}{data}\r\n"
            self.serial.write(cmd.encode())
            
        except Exception as e:
            self.logger.error(f"Error sending serial CAN message: {e}")
    
    def recv(self, timeout: float = 1.0) -> Optional[can.Message]:
        """Receive a CAN message via serial"""
        try:
            if not self.serial:
                return None
            
            # Read response
            response = self.serial.read(100).decode('ascii', errors='ignore')
            if not response:
                return None
            
            # Parse ELM327 response format
            if response.startswith('t'):
                # Extract CAN ID and data
                can_id = int(response[1:4], 16)
                data_len = int(response[4], 16)
                data = bytes.fromhex(response[5:5+data_len*2])
                
                return can.Message(
                    arbitration_id=can_id,
                    data=data
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error receiving serial CAN message: {e}")
            return None
    
    def shutdown(self):
        """Shutdown the serial interface"""
        try:
            if self.serial:
                self.serial.close()
                self.serial = None
        except Exception as e:
            self.logger.error(f"Error shutting down serial interface: {e}") 