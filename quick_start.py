#!/usr/bin/env python3
"""
Quick Start Script for ECU BIN Reader
Helps users get started with the application
"""

import sys
import subprocess
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version: {sys.version.split()[0]}")
        return True


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def check_obd2_adapter():
    """Check for OBD2 adapter availability"""
    print("\n🔌 Checking for OBD2 adapters...")
    
    try:
        import serial
        import serial.tools.list_ports
        
        ports = serial.tools.list_ports.comports()
        obd2_adapters = []
        
        for port in ports:
            description = (port.description or "").lower()
            if any(keyword in description for keyword in ["elm327", "obd", "diagnostic"]):
                obd2_adapters.append(port.device)
        
        if obd2_adapters:
            print(f"✅ Found {len(obd2_adapters)} OBD2 adapter(s):")
            for adapter in obd2_adapters:
                print(f"   - {adapter}")
        else:
            print("⚠️  No OBD2 adapters detected")
            print("   Make sure your OBD2 adapter is connected")
        
        return True
        
    except ImportError:
        print("⚠️  Could not check for OBD2 adapters (pyserial not installed)")
        return False


def run_tests():
    """Run basic tests"""
    print("\n🧪 Running tests...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "-v"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tests passed")
            return True
        else:
            print("⚠️  Some tests failed")
            print(result.stdout)
            return False
            
    except FileNotFoundError:
        print("⚠️  pytest not found, skipping tests")
        return True


def start_application():
    """Start the ECU BIN Reader application"""
    print("\n🚀 Starting ECU BIN Reader...")
    
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")


def show_usage_instructions():
    """Show usage instructions"""
    print("\n📖 Usage Instructions:")
    print("=" * 50)
    print("1. Connect your OBD2 adapter to your computer")
    print("2. Connect the adapter to your vehicle's OBD2 port")
    print("3. Start the application: python main.py")
    print("4. Click 'Scan Adapters' to detect your OBD2 adapter")
    print("5. Click 'Connect' to establish communication")
    print("6. Click 'Scan ECUs' to find available ECUs")
    print("7. Select an ECU and click 'Read BIN' to extract the binary")
    print("8. Save the BIN file for analysis or backup")
    print("\n⚠️  Important Notes:")
    print("- Ensure your vehicle supports OBD2")
    print("- Some ECUs may require security access")
    print("- Always backup your ECU before any modifications")
    print("- This tool is for educational purposes only")


def main():
    """Main quick start function"""
    print("ECU BIN Reader - Quick Start")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed. Please install dependencies manually:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Check for OBD2 adapter
    check_obd2_adapter()
    
    # Run tests
    run_tests()
    
    # Show usage instructions
    show_usage_instructions()
    
    # Ask if user wants to start the application
    print("\n" + "=" * 50)
    response = input("Would you like to start the ECU BIN Reader now? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        start_application()
    else:
        print("\nTo start the application later, run:")
        print("   python main.py")
        print("\nFor more information, see the README.md file")


if __name__ == "__main__":
    main() 