"""
KWP2000 (ISO 14230) protocol implementation
"""

import logging
import time
from typing import Optional, Dict, List
from src.protocols.can_bus import CANBus


class KWPProtocol:
    """KWP2000 (Keyword Protocol 2000) protocol implementation"""
    
    def __init__(self, can_bus: CANBus):
        self.can_bus = can_bus
        self.logger = logging.getLogger(__name__)
        
        # KWP constants
        self.SID_START_COMMUNICATION = 0x81
        self.SID_STOP_COMMUNICATION = 0x82
        self.SID_ECU_RESET = 0x83
        self.SID_READ_DATA_BY_LOCAL_IDENTIFIER = 0xA1
        self.SID_READ_DATA_BY_COMMON_IDENTIFIER = 0xA2
        self.SID_READ_MEMORY_BY_ADDRESS = 0xA3
        self.SID_READ_SCALING_DATA_BY_IDENTIFIER = 0xA4
        self.SID_READ_DATA_BY_PERIODIC_IDENTIFIER = 0xA5
        self.SID_DYNAMICALLY_DEFINE_DATA_IDENTIFIER = 0xA6
        self.SID_WRITE_DATA_BY_LOCAL_IDENTIFIER = 0xB1
        self.SID_WRITE_DATA_BY_COMMON_IDENTIFIER = 0xB2
        self.SID_WRITE_MEMORY_BY_ADDRESS = 0xB3
        self.SID_START_ROUTINE_BY_LOCAL_IDENTIFIER = 0xC1
        self.SID_START_ROUTINE_BY_ADDRESS = 0xC2
        self.SID_STOP_ROUTINE_BY_LOCAL_IDENTIFIER = 0xC3
        self.SID_STOP_ROUTINE_BY_ADDRESS = 0xC4
        self.SID_REQUEST_ROUTINE_RESULTS_BY_LOCAL_IDENTIFIER = 0xC5
        self.SID_REQUEST_ROUTINE_RESULTS_BY_ADDRESS = 0xC6
        self.SID_SECURITY_ACCESS = 0xE1
        self.SID_TRANSPORT_LAYER = 0xF0
        
        # Response codes
        self.NRC_POSITIVE_RESPONSE = 0xC1
        self.NRC_SERVICE_NOT_SUPPORTED = 0x11
        self.NRC_SUB_FUNCTION_NOT_SUPPORTED = 0x12
        self.NRC_INCORRECT_MESSAGE_LENGTH = 0x13
        self.NRC_CONDITIONS_NOT_CORRECT = 0x22
        self.NRC_REQUEST_SEQUENCE_ERROR = 0x24
        self.NRC_SECURITY_ACCESS_DENIED = 0x33
        self.NRC_INVALID_KEY = 0x35
        self.NRC_EXCEEDED_NUMBER_OF_ATTEMPTS = 0x36
        self.NRC_REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
        
    def send_start_communication(self, address: int) -> Optional[Dict]:
        """
        Send Start Communication (0x81)
        
        Args:
            address: ECU address
            
        Returns:
            Response dictionary or None
        """
        try:
            data = [self.SID_START_COMMUNICATION]
            response = self._send_kwp_message(address, data)
            
            if response and response.get('positive'):
                self.logger.info("KWP start communication successful")
            else:
                self.logger.warning(f"KWP start communication failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in KWP start communication: {e}")
            return None
    
    def send_stop_communication(self, address: int) -> Optional[Dict]:
        """
        Send Stop Communication (0x82)
        
        Args:
            address: ECU address
            
        Returns:
            Response dictionary or None
        """
        try:
            data = [self.SID_STOP_COMMUNICATION]
            response = self._send_kwp_message(address, data)
            
            if response and response.get('positive'):
                self.logger.info("KWP stop communication successful")
            else:
                self.logger.warning(f"KWP stop communication failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in KWP stop communication: {e}")
            return None
    
    def send_security_access(self, address: int, level: int, key: bytes = None) -> Optional[Dict]:
        """
        Send Security Access (0xE1)
        
        Args:
            address: ECU address
            level: Security level (odd=request seed, even=send key)
            key: Security key (for even levels)
            
        Returns:
            Response dictionary or None
        """
        try:
            if level % 2 == 1:  # Request seed
                data = [self.SID_SECURITY_ACCESS, level]
            else:  # Send key
                if not key:
                    self.logger.error("Key required for even security levels")
                    return None
                data = [self.SID_SECURITY_ACCESS, level] + list(key)
            
            response = self._send_kwp_message(address, data)
            
            if response and response.get('positive'):
                self.logger.info(f"KWP security access successful: level={level}")
            else:
                self.logger.warning(f"KWP security access failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in KWP security access: {e}")
            return None
    
    def read_data_by_local_identifier(self, address: int, identifier: int) -> Optional[Dict]:
        """
        Read Data by Local Identifier (0xA1)
        
        Args:
            address: ECU address
            identifier: Local identifier
            
        Returns:
            Response dictionary or None
        """
        try:
            data = [self.SID_READ_DATA_BY_LOCAL_IDENTIFIER, identifier]
            response = self._send_kwp_message(address, data)
            
            if response and response.get('positive'):
                self.logger.info(f"KWP read data by local identifier successful: id=0x{identifier:02X}")
            else:
                self.logger.warning(f"KWP read data by local identifier failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in KWP read data by local identifier: {e}")
            return None
    
    def read_data_by_common_identifier(self, address: int, identifier: int) -> Optional[Dict]:
        """
        Read Data by Common Identifier (0xA2)
        
        Args:
            address: ECU address
            identifier: Common identifier
            
        Returns:
            Response dictionary or None
        """
        try:
            data = [self.SID_READ_DATA_BY_COMMON_IDENTIFIER, (identifier >> 8) & 0xFF, identifier & 0xFF]
            response = self._send_kwp_message(address, data)
            
            if response and response.get('positive'):
                self.logger.info(f"KWP read data by common identifier successful: id=0x{identifier:04X}")
            else:
                self.logger.warning(f"KWP read data by common identifier failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in KWP read data by common identifier: {e}")
            return None
    
    def read_memory_by_address(self, address: int, memory_address: int, size: int) -> Optional[bytes]:
        """
        Read Memory by Address (0xA3)
        
        Args:
            address: ECU address
            memory_address: Memory address to read
            size: Number of bytes to read
            
        Returns:
            Memory data or None
        """
        try:
            # Format memory address and size
            addr_bytes = self._format_address(memory_address)
            size_bytes = self._format_size(size)
            
            data = [self.SID_READ_MEMORY_BY_ADDRESS] + addr_bytes + size_bytes
            response = self._send_kwp_message(address, data)
            
            if response and response.get('positive'):
                memory_data = response.get('data', b'')
                self.logger.info(f"KWP read memory successful: addr=0x{memory_address:08X}, size={size}")
                return memory_data
            else:
                self.logger.warning(f"KWP read memory failed: {response}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in KWP read memory by address: {e}")
            return None
    
    def write_memory_by_address(self, address: int, memory_address: int, data: bytes) -> Optional[Dict]:
        """
        Write Memory by Address (0xB3)
        
        Args:
            address: ECU address
            memory_address: Memory address to write
            data: Data to write
            
        Returns:
            Response dictionary or None
        """
        try:
            # Format memory address and size
            addr_bytes = self._format_address(memory_address)
            size_bytes = self._format_size(len(data))
            
            message_data = [self.SID_WRITE_MEMORY_BY_ADDRESS] + addr_bytes + size_bytes + list(data)
            response = self._send_kwp_message(address, message_data)
            
            if response and response.get('positive'):
                self.logger.info(f"KWP write memory successful: addr=0x{memory_address:08X}, size={len(data)}")
            else:
                self.logger.warning(f"KWP write memory failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in KWP write memory by address: {e}")
            return None
    
    def start_routine_by_local_identifier(self, address: int, routine_id: int, data: bytes = None) -> Optional[Dict]:
        """
        Start Routine by Local Identifier (0xC1)
        
        Args:
            address: ECU address
            routine_id: Routine identifier
            data: Optional routine data
            
        Returns:
            Response dictionary or None
        """
        try:
            message_data = [self.SID_START_ROUTINE_BY_LOCAL_IDENTIFIER, routine_id]
            if data:
                message_data.extend(data)
            
            response = self._send_kwp_message(address, message_data)
            
            if response and response.get('positive'):
                self.logger.info(f"KWP start routine successful: id=0x{routine_id:02X}")
            else:
                self.logger.warning(f"KWP start routine failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in KWP start routine: {e}")
            return None
    
    def _send_kwp_message(self, address: int, data: List[int]) -> Optional[Dict]:
        """
        Send KWP message and wait for response
        
        Args:
            address: ECU address
            data: Message data
            
        Returns:
            Response dictionary or None
        """
        try:
            # Send message
            if not self.can_bus.send_message(address, data):
                return None
            
            # Wait for response
            response = self.can_bus.receive_message(timeout=2.0)
            if not response:
                return None
            
            # Parse response
            return self._parse_kwp_response(response)
            
        except Exception as e:
            self.logger.error(f"Error sending KWP message: {e}")
            return None
    
    def _parse_kwp_response(self, message) -> Optional[Dict]:
        """
        Parse KWP response message
        
        Args:
            message: CAN message
            
        Returns:
            Parsed response dictionary
        """
        try:
            if not message or not message.data:
                return None
            
            data = list(message.data)
            if len(data) < 1:
                return None
            
            # Check for positive response
            if data[0] == self.NRC_POSITIVE_RESPONSE:
                return {
                    'positive': True,
                    'sid': data[1] if len(data) > 1 else None,
                    'data': bytes(data[2:]) if len(data) > 2 else b''
                }
            
            # Check for negative response
            elif data[0] == 0xBF:
                if len(data) >= 3:
                    return {
                        'positive': False,
                        'sid': data[1],
                        'nrc': data[2],
                        'error': self._get_nrc_description(data[2])
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing KWP response: {e}")
            return None
    
    def _format_address(self, address: int) -> List[int]:
        """Format memory address for KWP message"""
        if address <= 0xFF:
            return [0x01, address]
        elif address <= 0xFFFF:
            return [0x02, (address >> 8) & 0xFF, address & 0xFF]
        elif address <= 0xFFFFFF:
            return [0x03, (address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF]
        else:
            return [0x04, (address >> 24) & 0xFF, (address >> 16) & 0xFF, 
                   (address >> 8) & 0xFF, address & 0xFF]
    
    def _format_size(self, size: int) -> List[int]:
        """Format size for KWP message"""
        if size <= 0xFF:
            return [0x01, size]
        elif size <= 0xFFFF:
            return [0x02, (size >> 8) & 0xFF, size & 0xFF]
        elif size <= 0xFFFFFF:
            return [0x03, (size >> 16) & 0xFF, (size >> 8) & 0xFF, size & 0xFF]
        else:
            return [0x04, (size >> 24) & 0xFF, (size >> 16) & 0xFF, 
                   (size >> 8) & 0xFF, size & 0xFF]
    
    def _get_nrc_description(self, nrc: int) -> str:
        """Get description for negative response code"""
        nrc_descriptions = {
            self.NRC_SERVICE_NOT_SUPPORTED: "Service not supported",
            self.NRC_SUB_FUNCTION_NOT_SUPPORTED: "Sub-function not supported",
            self.NRC_INCORRECT_MESSAGE_LENGTH: "Incorrect message length",
            self.NRC_CONDITIONS_NOT_CORRECT: "Conditions not correct",
            self.NRC_REQUEST_SEQUENCE_ERROR: "Request sequence error",
            self.NRC_SECURITY_ACCESS_DENIED: "Security access denied",
            self.NRC_INVALID_KEY: "Invalid key",
            self.NRC_EXCEEDED_NUMBER_OF_ATTEMPTS: "Exceeded number of attempts",
            self.NRC_REQUIRED_TIME_DELAY_NOT_EXPIRED: "Required time delay not expired"
        }
        return nrc_descriptions.get(nrc, f"Unknown NRC: 0x{nrc:02X}") 