"""
Unit tests for ECU Manager
"""

import unittest
from unittest.mock import Mock, patch
from src.core.ecu_manager import ECUManger, ECUInfo, BINReadProgress
from src.utils.obd2_adapters import OBD2Adapter


class TestECUManager(unittest.TestCase):
    """Test cases for ECU Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_adapter = Mock(spec=OBD2Adapter)
        self.mock_adapter.port = "/dev/ttyUSB0"
        self.mock_adapter.description = "Test OBD2 Adapter"
        
        self.ecu_manager = ECUManger(self.mock_adapter)
    
    def test_ecu_manager_initialization(self):
        """Test ECU manager initialization"""
        self.assertIsNotNone(self.ecu_manager)
        self.assertEqual(self.ecu_manager.adapter, self.mock_adapter)
        self.assertEqual(len(self.ecu_manager.discovered_ecus), 0)
        self.assertIsNone(self.ecu_manager.selected_ecu)
    
    def test_ecu_info_creation(self):
        """Test ECU info creation"""
        ecu_info = ECUInfo(
            ecu_id="TEST_ECU",
            protocol="UDS",
            address=0x7E0,
            vin="TEST123456789",
            manufacturer="Test Manufacturer"
        )
        
        self.assertEqual(ecu_info.ecu_id, "TEST_ECU")
        self.assertEqual(ecu_info.protocol, "UDS")
        self.assertEqual(ecu_info.address, 0x7E0)
        self.assertEqual(ecu_info.vin, "TEST123456789")
        self.assertEqual(ecu_info.manufacturer, "Test Manufacturer")
    
    def test_bin_read_progress_creation(self):
        """Test BIN read progress creation"""
        progress = BINReadProgress(
            bytes_read=1024,
            total_bytes=8192,
            current_address=0x1000,
            status="reading"
        )
        
        self.assertEqual(progress.bytes_read, 1024)
        self.assertEqual(progress.total_bytes, 8192)
        self.assertEqual(progress.current_address, 0x1000)
        self.assertEqual(progress.status, "reading")
    
    @patch('src.core.ecu_manager.CANBus')
    @patch('src.core.ecu_manager.UDSProtocol')
    @patch('src.core.ecu_manager.KWPProtocol')
    def test_initialize_communication_success(self, mock_kwp, mock_uds, mock_can):
        """Test successful communication initialization"""
        # Mock CAN bus connection
        mock_can_instance = Mock()
        mock_can_instance.connect.return_value = True
        mock_can.return_value = mock_can_instance
        
        # Mock protocols
        mock_uds_instance = Mock()
        mock_kwp_instance = Mock()
        mock_uds.return_value = mock_uds_instance
        mock_kwp.return_value = mock_kwp_instance
        
        result = self.ecu_manager.initialize_communication()
        
        self.assertTrue(result)
        mock_can_instance.connect.assert_called_once()
    
    @patch('src.core.ecu_manager.CANBus')
    def test_initialize_communication_failure(self, mock_can):
        """Test failed communication initialization"""
        # Mock CAN bus connection failure
        mock_can_instance = Mock()
        mock_can_instance.connect.return_value = False
        mock_can.return_value = mock_can_instance
        
        result = self.ecu_manager.initialize_communication()
        
        self.assertFalse(result)
    
    def test_scan_ecus_empty(self):
        """Test ECU scanning with no ECUs found"""
        # Mock the probe method to return None
        self.ecu_manager._probe_ecu = Mock(return_value=None)
        
        result = self.ecu_manager.scan_ecus()
        
        self.assertEqual(len(result), 0)
        self.assertEqual(len(self.ecu_manager.discovered_ecus), 0)
    
    def test_scan_ecus_with_results(self):
        """Test ECU scanning with ECUs found"""
        # Mock ECU info
        mock_ecu = ECUInfo(
            ecu_id="TEST_ECU",
            protocol="UDS",
            address=0x7E0
        )
        
        # Mock the probe method to return an ECU
        self.ecu_manager._probe_ecu = Mock(return_value=mock_ecu)
        
        result = self.ecu_manager.scan_ecus()
        
        self.assertEqual(len(result), 16)  # 0x7E0-0x7EF range
        self.assertEqual(len(self.ecu_manager.discovered_ecus), 16)
    
    def test_select_ecu_success(self):
        """Test successful ECU selection"""
        ecu_info = ECUInfo(
            ecu_id="TEST_ECU",
            protocol="UDS",
            address=0x7E0
        )
        
        # Mock the get ECU details method
        self.ecu_manager._get_ecu_details = Mock()
        
        result = self.ecu_manager.select_ecu(ecu_info)
        
        self.assertTrue(result)
        self.assertEqual(self.ecu_manager.selected_ecu, ecu_info)
    
    def test_save_bin_file_no_data(self):
        """Test saving BIN file with no data"""
        result = self.ecu_manager.save_bin_file()
        
        self.assertFalse(result)
    
    def test_save_bin_file_with_data(self):
        """Test saving BIN file with data"""
        # Add some test data
        self.ecu_manager.bin_data = b"test binary data"
        self.ecu_manager.selected_ecu = ECUInfo(
            ecu_id="TEST_ECU",
            protocol="UDS",
            address=0x7E0,
            vin="TEST123"
        )
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = self.ecu_manager.save_bin_file("test.bin")
            
            self.assertTrue(result)
            mock_file.write.assert_called_once_with(b"test binary data")
    
    def test_get_progress(self):
        """Test getting progress information"""
        progress = self.ecu_manager.get_progress()
        
        self.assertIsInstance(progress, BINReadProgress)
        self.assertEqual(progress.status, "idle")
        self.assertEqual(progress.bytes_read, 0)
        self.assertEqual(progress.total_bytes, 0)


if __name__ == '__main__':
    unittest.main() 