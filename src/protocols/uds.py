"""
UDS (ISO 14229) protocol implementation
"""

import logging
import time
from typing import Optional, Dict, List
from src.protocols.can_bus import CANBus


class UDSProtocol:
    """UDS (Unified Diagnostic Services) protocol implementation"""
    
    def __init__(self, can_bus: CANBus):
        self.can_bus = can_bus
        self.logger = logging.getLogger(__name__)
        
        # UDS constants
        self.SID_DIAGNOSTIC_SESSION_CONTROL = 0x10
        self.SID_ECU_RESET = 0x11
        self.SID_SECURITY_ACCESS = 0x27
        self.SID_COMMUNICATION_CONTROL = 0x28
        self.SID_READ_DATA_BY_IDENTIFIER = 0x22
        self.SID_READ_MEMORY_BY_ADDRESS = 0x23
        self.SID_WRITE_MEMORY_BY_ADDRESS = 0x3D
        self.SID_ROUTINE_CONTROL = 0x31
        self.SID_REQUEST_DOWNLOAD = 0x34
        self.SID_REQUEST_UPLOAD = 0x35
        self.SID_TRANSFER_DATA = 0x36
        self.SID_REQUEST_TRANSFER_EXIT = 0x37
        
        # Response codes
        self.NRC_POSITIVE_RESPONSE = 0x40
        self.NRC_SERVICE_NOT_SUPPORTED = 0x11
        self.NRC_SUB_FUNCTION_NOT_SUPPORTED = 0x12
        self.NRC_INCORRECT_MESSAGE_LENGTH = 0x13
        self.NRC_CONDITIONS_NOT_CORRECT = 0x22
        self.NRC_REQUEST_SEQUENCE_ERROR = 0x24
        self.NRC_SECURITY_ACCESS_DENIED = 0x33
        self.NRC_INVALID_KEY = 0x35
        self.NRC_EXCEEDED_NUMBER_OF_ATTEMPTS = 0x36
        self.NRC_REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
        self.NRC_GENERAL_PROGRAMMING_FAILURE = 0x72
        self.NRC_WRONG_BLOCK_SEQUENCE_COUNTER = 0x73
        self.NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x7F
        
    def send_diagnostic_session_control(self, address: int, session_type: int) -> Optional[Dict]:
        """
        Send Diagnostic Session Control (0x10)
        
        Args:
            address: ECU address
            session_type: Session type (0x01=default, 0x02=programming, 0x03=extended)
            
        Returns:
            Response dictionary or None
        """
        try:
            data = [self.SID_DIAGNOSTIC_SESSION_CONTROL, session_type]
            response = self._send_uds_message(address, data)
            
            if response and response.get('positive'):
                self.logger.info(f"Diagnostic session control successful: session={session_type}")
            else:
                self.logger.warning(f"Diagnostic session control failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in diagnostic session control: {e}")
            return None
    
    def send_security_access(self, address: int, level: int, key: bytes = None) -> Optional[Dict]:
        """
        Send Security Access (0x27)
        
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
            
            response = self._send_uds_message(address, data)
            
            if response and response.get('positive'):
                self.logger.info(f"Security access successful: level={level}")
            else:
                self.logger.warning(f"Security access failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in security access: {e}")
            return None
    
    def read_data_by_identifier(self, address: int, identifier: int) -> Optional[Dict]:
        """
        Read Data by Identifier (0x22)
        
        Args:
            address: ECU address
            identifier: Data identifier
            
        Returns:
            Response dictionary or None
        """
        try:
            data = [self.SID_READ_DATA_BY_IDENTIFIER, (identifier >> 8) & 0xFF, identifier & 0xFF]
            response = self._send_uds_message(address, data)
            
            if response and response.get('positive'):
                self.logger.info(f"Read data by identifier successful: id=0x{identifier:04X}")
            else:
                self.logger.warning(f"Read data by identifier failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in read data by identifier: {e}")
            return None
    
    def read_memory_by_address(self, address: int, memory_address: int, size: int) -> Optional[bytes]:
        """
        Read Memory by Address (0x23)
        
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
            response = self._send_uds_message(address, data)
            
            if response and response.get('positive'):
                memory_data = response.get('data', b'')
                self.logger.info(f"Read memory successful: addr=0x{memory_address:08X}, size={size}")
                return memory_data
            else:
                self.logger.warning(f"Read memory failed: {response}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in read memory by address: {e}")
            return None
    
    def write_memory_by_address(self, address: int, memory_address: int, data: bytes) -> Optional[Dict]:
        """
        Write Memory by Address (0x3D)
        
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
            response = self._send_uds_message(address, message_data)
            
            if response and response.get('positive'):
                self.logger.info(f"Write memory successful: addr=0x{memory_address:08X}, size={len(data)}")
            else:
                self.logger.warning(f"Write memory failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in write memory by address: {e}")
            return None
    
    def routine_control(self, address: int, routine_type: int, routine_id: int, data: bytes = None) -> Optional[Dict]:
        """
        Routine Control (0x31)
        
        Args:
            address: ECU address
            routine_type: Routine type (0x01=start, 0x02=stop, 0x03=request results)
            routine_id: Routine identifier
            data: Optional routine data
            
        Returns:
            Response dictionary or None
        """
        try:
            message_data = [self.SID_ROUTINE_CONTROL, routine_type, (routine_id >> 8) & 0xFF, routine_id & 0xFF]
            if data:
                message_data.extend(data)
            
            response = self._send_uds_message(address, message_data)
            
            if response and response.get('positive'):
                self.logger.info(f"Routine control successful: type={routine_type}, id=0x{routine_id:04X}")
            else:
                self.logger.warning(f"Routine control failed: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in routine control: {e}")
            return None
    
    def _send_uds_message(self, address: int, data: List[int]) -> Optional[Dict]:
        """
        Send UDS message and wait for response
        
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
            return self._parse_uds_response(response)
            
        except Exception as e:
            self.logger.error(f"Error sending UDS message: {e}")
            return None
    
    def _parse_uds_response(self, message) -> Optional[Dict]:
        """
        Parse UDS response message
        
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
            elif data[0] == 0x7F:
                if len(data) >= 3:
                    return {
                        'positive': False,
                        'sid': data[1],
                        'nrc': data[2],
                        'error': self._get_nrc_description(data[2])
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing UDS response: {e}")
            return None
    
    def _format_address(self, address: int) -> List[int]:
        """Format memory address for UDS message"""
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
        """Format size for UDS message"""
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
            self.NRC_REQUIRED_TIME_DELAY_NOT_EXPIRED: "Required time delay not expired",
            self.NRC_GENERAL_PROGRAMMING_FAILURE: "General programming failure",
            self.NRC_WRONG_BLOCK_SEQUENCE_COUNTER: "Wrong block sequence counter",
            self.NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING: "Request correctly received, response pending"
        }
        return nrc_descriptions.get(nrc, f"Unknown NRC: 0x{nrc:02X}") 