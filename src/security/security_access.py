"""
Security Access module for ECU communication
Handles seed/key algorithms for different ECU types
"""

import logging
import time
import hashlib
from typing import Optional, Dict, List
from src.protocols.uds import UDSProtocol
from src.protocols.kwp import KWPProtocol


class SecurityAccess:
    """Security Access handler for ECU communication"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.seed_key_algorithms = {
            'default': self._default_seed_key_algorithm,
            'bmw': self._bmw_seed_key_algorithm,
            'audi': self._audi_seed_key_algorithm,
            'mercedes': self._mercedes_seed_key_algorithm,
            'volkswagen': self._volkswagen_seed_key_algorithm,
            'toyota': self._toyota_seed_key_algorithm,
            'honda': self._honda_seed_key_algorithm,
            'ford': self._ford_seed_key_algorithm,
            'gm': self._gm_seed_key_algorithm,
        }
    
    def perform_uds_security_access(self, uds_protocol: UDSProtocol, address: int, 
                                  algorithm: str = 'default') -> bool:
        """
        Perform UDS security access
        
        Args:
            uds_protocol: UDS protocol instance
            address: ECU address
            algorithm: Seed/key algorithm to use
            
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Starting UDS security access with algorithm: {algorithm}")
            
            # Get the seed/key algorithm
            seed_key_func = self.seed_key_algorithms.get(algorithm, self._default_seed_key_algorithm)
            
            # Try different security levels
            for level in [1, 2, 3, 5, 7]:  # Common security levels
                if self._perform_security_level(uds_protocol, address, level, seed_key_func):
                    self.logger.info(f"UDS security access successful at level {level}")
                    return True
            
            self.logger.warning("UDS security access failed at all levels")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in UDS security access: {e}")
            return False
    
    def perform_kwp_security_access(self, kwp_protocol: KWPProtocol, address: int,
                                  algorithm: str = 'default') -> bool:
        """
        Perform KWP security access
        
        Args:
            kwp_protocol: KWP protocol instance
            address: ECU address
            algorithm: Seed/key algorithm to use
            
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Starting KWP security access with algorithm: {algorithm}")
            
            # Get the seed/key algorithm
            seed_key_func = self.seed_key_algorithms.get(algorithm, self._default_seed_key_algorithm)
            
            # Try different security levels
            for level in [1, 2, 3, 5, 7]:  # Common security levels
                if self._perform_kwp_security_level(kwp_protocol, address, level, seed_key_func):
                    self.logger.info(f"KWP security access successful at level {level}")
                    return True
            
            self.logger.warning("KWP security access failed at all levels")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in KWP security access: {e}")
            return False
    
    def _perform_security_level(self, uds_protocol: UDSProtocol, address: int, 
                               level: int, seed_key_func) -> bool:
        """
        Perform security access at a specific level
        
        Args:
            uds_protocol: UDS protocol instance
            address: ECU address
            level: Security level
            seed_key_func: Seed/key algorithm function
            
        Returns:
            True if successful
        """
        try:
            # Request seed (odd level)
            seed_level = level if level % 2 == 1 else level - 1
            seed_response = uds_protocol.send_security_access(address, seed_level)
            
            if not seed_response or not seed_response.get('positive'):
                self.logger.debug(f"Seed request failed at level {seed_level}")
                return False
            
            # Extract seed from response
            seed_data = seed_response.get('data', b'')
            if not seed_data:
                self.logger.debug(f"No seed data received at level {seed_level}")
                return False
            
            # Calculate key from seed
            key = seed_key_func(seed_data, level)
            if not key:
                self.logger.debug(f"Key calculation failed for level {level}")
                return False
            
            # Send key (even level)
            key_level = level if level % 2 == 0 else level + 1
            key_response = uds_protocol.send_security_access(address, key_level, key)
            
            if key_response and key_response.get('positive'):
                return True
            
            # Wait before retry if needed
            if key_response and key_response.get('nrc') == 0x37:  # Time delay
                time.sleep(1)
                key_response = uds_protocol.send_security_access(address, key_level, key)
                return key_response and key_response.get('positive')
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in security level {level}: {e}")
            return False
    
    def _perform_kwp_security_level(self, kwp_protocol: KWPProtocol, address: int,
                                   level: int, seed_key_func) -> bool:
        """
        Perform KWP security access at a specific level
        
        Args:
            kwp_protocol: KWP protocol instance
            address: ECU address
            level: Security level
            seed_key_func: Seed/key algorithm function
            
        Returns:
            True if successful
        """
        try:
            # Request seed (odd level)
            seed_level = level if level % 2 == 1 else level - 1
            seed_response = kwp_protocol.send_security_access(address, seed_level)
            
            if not seed_response or not seed_response.get('positive'):
                self.logger.debug(f"KWP seed request failed at level {seed_level}")
                return False
            
            # Extract seed from response
            seed_data = seed_response.get('data', b'')
            if not seed_data:
                self.logger.debug(f"No KWP seed data received at level {seed_level}")
                return False
            
            # Calculate key from seed
            key = seed_key_func(seed_data, level)
            if not key:
                self.logger.debug(f"KWP key calculation failed for level {level}")
                return False
            
            # Send key (even level)
            key_level = level if level % 2 == 0 else level + 1
            key_response = kwp_protocol.send_security_access(address, key_level, key)
            
            if key_response and key_response.get('positive'):
                return True
            
            # Wait before retry if needed
            if key_response and key_response.get('nrc') == 0x37:  # Time delay
                time.sleep(1)
                key_response = kwp_protocol.send_security_access(address, key_level, key)
                return key_response and key_response.get('positive')
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in KWP security level {level}: {e}")
            return False
    
    def _default_seed_key_algorithm(self, seed: bytes, level: int) -> Optional[bytes]:
        """
        Default seed/key algorithm (simple XOR)
        
        Args:
            seed: Seed data from ECU
            level: Security level
            
        Returns:
            Calculated key or None
        """
        try:
            if not seed:
                return None
            
            # Simple XOR algorithm
            key = bytearray(len(seed))
            for i in range(len(seed)):
                key[i] = seed[i] ^ 0x55 ^ level
            
            return bytes(key)
            
        except Exception as e:
            self.logger.error(f"Error in default seed/key algorithm: {e}")
            return None
    
    def _bmw_seed_key_algorithm(self, seed: bytes, level: int) -> Optional[bytes]:
        """
        BMW seed/key algorithm
        
        Args:
            seed: Seed data from ECU
            level: Security level
            
        Returns:
            Calculated key or None
        """
        try:
            if len(seed) < 4:
                return None
            
            # BMW algorithm (simplified)
            key = bytearray(4)
            seed_int = int.from_bytes(seed[:4], 'big')
            
            # BMW-specific calculation
            key_int = (seed_int * 0x12345678 + 0x87654321) & 0xFFFFFFFF
            key_int ^= level
            
            key = key_int.to_bytes(4, 'big')
            return key
            
        except Exception as e:
            self.logger.error(f"Error in BMW seed/key algorithm: {e}")
            return None
    
    def _audi_seed_key_algorithm(self, seed: bytes, level: int) -> Optional[bytes]:
        """
        Audi seed/key algorithm
        
        Args:
            seed: Seed data from ECU
            level: Security level
            
        Returns:
            Calculated key or None
        """
        try:
            if len(seed) < 4:
                return None
            
            # Audi algorithm (simplified)
            key = bytearray(4)
            seed_int = int.from_bytes(seed[:4], 'big')
            
            # Audi-specific calculation
            key_int = (seed_int + 0x12345678) & 0xFFFFFFFF
            key_int = ((key_int << 3) | (key_int >> 29)) & 0xFFFFFFFF
            key_int ^= level
            
            key = key_int.to_bytes(4, 'big')
            return key
            
        except Exception as e:
            self.logger.error(f"Error in Audi seed/key algorithm: {e}")
            return None
    
    def _mercedes_seed_key_algorithm(self, seed: bytes, level: int) -> Optional[bytes]:
        """
        Mercedes seed/key algorithm
        
        Args:
            seed: Seed data from ECU
            level: Security level
            
        Returns:
            Calculated key or None
        """
        try:
            if len(seed) < 4:
                return None
            
            # Mercedes algorithm (simplified)
            key = bytearray(4)
            seed_int = int.from_bytes(seed[:4], 'big')
            
            # Mercedes-specific calculation
            key_int = (seed_int * 0x23456789) & 0xFFFFFFFF
            key_int = ((key_int << 7) | (key_int >> 25)) & 0xFFFFFFFF
            key_int ^= level
            
            key = key_int.to_bytes(4, 'big')
            return key
            
        except Exception as e:
            self.logger.error(f"Error in Mercedes seed/key algorithm: {e}")
            return None
    
    def _volkswagen_seed_key_algorithm(self, seed: bytes, level: int) -> Optional[bytes]:
        """
        Volkswagen seed/key algorithm
        
        Args:
            seed: Seed data from ECU
            level: Security level
            
        Returns:
            Calculated key or None
        """
        try:
            if len(seed) < 4:
                return None
            
            # VW algorithm (simplified)
            key = bytearray(4)
            seed_int = int.from_bytes(seed[:4], 'big')
            
            # VW-specific calculation
            key_int = (seed_int ^ 0x34567890) & 0xFFFFFFFF
            key_int = ((key_int << 5) | (key_int >> 27)) & 0xFFFFFFFF
            key_int += level
            
            key = key_int.to_bytes(4, 'big')
            return key
            
        except Exception as e:
            self.logger.error(f"Error in Volkswagen seed/key algorithm: {e}")
            return None
    
    def _toyota_seed_key_algorithm(self, seed: bytes, level: int) -> Optional[bytes]:
        """
        Toyota seed/key algorithm
        
        Args:
            seed: Seed data from ECU
            level: Security level
            
        Returns:
            Calculated key or None
        """
        try:
            if len(seed) < 4:
                return None
            
            # Toyota algorithm (simplified)
            key = bytearray(4)
            seed_int = int.from_bytes(seed[:4], 'big')
            
            # Toyota-specific calculation
            key_int = (seed_int + 0x45678901) & 0xFFFFFFFF
            key_int = ((key_int << 11) | (key_int >> 21)) & 0xFFFFFFFF
            key_int ^= level
            
            key = key_int.to_bytes(4, 'big')
            return key
            
        except Exception as e:
            self.logger.error(f"Error in Toyota seed/key algorithm: {e}")
            return None
    
    def _honda_seed_key_algorithm(self, seed: bytes, level: int) -> Optional[bytes]:
        """
        Honda seed/key algorithm
        
        Args:
            seed: Seed data from ECU
            level: Security level
            
        Returns:
            Calculated key or None
        """
        try:
            if len(seed) < 4:
                return None
            
            # Honda algorithm (simplified)
            key = bytearray(4)
            seed_int = int.from_bytes(seed[:4], 'big')
            
            # Honda-specific calculation
            key_int = (seed_int * 0x56789012) & 0xFFFFFFFF
            key_int = ((key_int << 13) | (key_int >> 19)) & 0xFFFFFFFF
            key_int += level
            
            key = key_int.to_bytes(4, 'big')
            return key
            
        except Exception as e:
            self.logger.error(f"Error in Honda seed/key algorithm: {e}")
            return None
    
    def _ford_seed_key_algorithm(self, seed: bytes, level: int) -> Optional[bytes]:
        """
        Ford seed/key algorithm
        
        Args:
            seed: Seed data from ECU
            level: Security level
            
        Returns:
            Calculated key or None
        """
        try:
            if len(seed) < 4:
                return None
            
            # Ford algorithm (simplified)
            key = bytearray(4)
            seed_int = int.from_bytes(seed[:4], 'big')
            
            # Ford-specific calculation
            key_int = (seed_int ^ 0x67890123) & 0xFFFFFFFF
            key_int = ((key_int << 17) | (key_int >> 15)) & 0xFFFFFFFF
            key_int ^= level
            
            key = key_int.to_bytes(4, 'big')
            return key
            
        except Exception as e:
            self.logger.error(f"Error in Ford seed/key algorithm: {e}")
            return None
    
    def _gm_seed_key_algorithm(self, seed: bytes, level: int) -> Optional[bytes]:
        """
        GM seed/key algorithm
        
        Args:
            seed: Seed data from ECU
            level: Security level
            
        Returns:
            Calculated key or None
        """
        try:
            if len(seed) < 4:
                return None
            
            # GM algorithm (simplified)
            key = bytearray(4)
            seed_int = int.from_bytes(seed[:4], 'big')
            
            # GM-specific calculation
            key_int = (seed_int + 0x78901234) & 0xFFFFFFFF
            key_int = ((key_int << 19) | (key_int >> 13)) & 0xFFFFFFFF
            key_int += level
            
            key = key_int.to_bytes(4, 'big')
            return key
            
        except Exception as e:
            self.logger.error(f"Error in GM seed/key algorithm: {e}")
            return None
    
    def add_custom_algorithm(self, name: str, algorithm_func):
        """
        Add a custom seed/key algorithm
        
        Args:
            name: Algorithm name
            algorithm_func: Algorithm function (seed, level) -> key
        """
        self.seed_key_algorithms[name] = algorithm_func
        self.logger.info(f"Added custom seed/key algorithm: {name}")
    
    def get_available_algorithms(self) -> List[str]:
        """Get list of available seed/key algorithms"""
        return list(self.seed_key_algorithms.keys()) 