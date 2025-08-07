#!/usr/bin/env python3
"""
Windows build script for ECU BIN Reader
Creates a standalone executable with PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def create_app_icon():
    """Create a simple app icon if none exists"""
    
    # Create assets directory if it doesn't exist
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    # Create a simple icon file (this is a placeholder - you should replace with a real icon)
    icon_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" fill="#2c3e50" rx="64"/>
  <circle cx="256" cy="200" r="80" fill="#3498db"/>
  <rect x="176" y="320" width="160" height="120" fill="#e74c3c" rx="16"/>
  <text x="256" y="420" text-anchor="middle" fill="white" font-family="Arial" font-size="24">ECU</text>
</svg>"""
    
    icon_path = assets_dir / "icon.svg"
    with open(icon_path, "w") as f:
        f.write(icon_content)
    
    print(f"Created placeholder icon: {icon_path}")
    print("Note: Replace with a proper .ico file for production")


def build_windows_executable():
    """Build Windows executable using PyInstaller"""
    
    print("Building ECU BIN Reader for Windows...")
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Create build directory
    build_dir = project_root / "build" / "windows"
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Single executable
        "--windowed",  # No console window
        "--name=ECU_BIN_Reader",
        "--distpath", str(build_dir),
        "--workpath", str(build_dir / "work"),
        "--specpath", str(build_dir),

        "--hidden-import", "can",
        "--hidden-import", "cantools",
        "--hidden-import", "serial",
        "--hidden-import", "PyQt5",
        "--hidden-import", "cryptography",
        "--hidden-import", "numpy",
        "--hidden-import", "pandas",
        "main.py"
    ]
    
    # Add icon if available
    icon_path = project_root / "assets" / "icon.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        print(f"Using icon: {icon_path}")
    else:
        print("No icon file found, using default")
    
    try:
        # Run PyInstaller
        print("Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("PyInstaller completed successfully")
        
        # Check if executable was created
        exe_path = build_dir / "ECU_BIN_Reader.exe"
        if exe_path.exists():
            print(f"Executable created: {exe_path}")
            
            # Create installer directory
            installer_dir = build_dir / "installer"
            installer_dir.mkdir(exist_ok=True)
            
            # Copy executable to installer directory
            shutil.copy2(exe_path, installer_dir / "ECU_BIN_Reader.exe")
            
            # Copy additional files
            if (project_root / "README.md").exists():
                shutil.copy2(project_root / "README.md", installer_dir)
            
            if (project_root / "LICENSE").exists():
                shutil.copy2(project_root / "LICENSE", installer_dir)
            
            # Create batch file for easy execution
            batch_content = """@echo off
echo Starting ECU BIN Reader...
ECU_BIN_Reader.exe
pause
"""
            with open(installer_dir / "run.bat", "w") as f:
                f.write(batch_content)
            
            print(f"Installer package created in: {installer_dir}")
            print("To create a proper installer, use NSIS or similar tools")
            
        else:
            print("Error: Executable not found")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Build error: {e}")
        return False
    
    return True


def create_nsis_installer():
    """Create NSIS installer script"""
    
    nsis_script = """
!define APP_NAME "ECU BIN Reader"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "ECU Tools"
!define APP_EXE "ECU_BIN_Reader.exe"

!include "MUI2.nsh"

Name "${APP_NAME}"
OutFile "ECU_BIN_Reader_Setup.exe"
InstallDir "$PROGRAMFILES\\${APP_NAME}"
InstallDirRegKey HKCU "Software\\${APP_NAME}" ""

!define MUI_ABORTWARNING
!define MUI_ICON "assets\\icon.ico"
!define MUI_UNICON "assets\\icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Main Application" SecMain
    SetOutPath "$INSTDIR"
    File "ECU_BIN_Reader.exe"
    File "README.md"
    File "LICENSE"
    File "run.bat"
    
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    
    CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
    CreateShortCut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    
    WriteRegStr HKCU "Software\\${APP_NAME}" "" $INSTDIR
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayIcon" "$INSTDIR\\${APP_EXE}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\${APP_EXE}"
    Delete "$INSTDIR\\README.md"
    Delete "$INSTDIR\\LICENSE"
    Delete "$INSTDIR\\run.bat"
    Delete "$INSTDIR\\Uninstall.exe"
    
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\\${APP_NAME}\\Uninstall.lnk"
    RMDir "$SMPROGRAMS\\${APP_NAME}"
    Delete "$DESKTOP\\${APP_NAME}.lnk"
    
    DeleteRegKey HKCU "Software\\${APP_NAME}"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
SectionEnd
"""
    
    build_dir = Path(__file__).parent / "build" / "windows" / "installer"
    nsis_file = build_dir / "installer.nsi"
    
    with open(nsis_file, "w") as f:
        f.write(nsis_script)
    
    print(f"NSIS script created: {nsis_file}")
    print("To create installer, run: makensis installer.nsi")


def main():
    """Main build function"""
    
    print("ECU BIN Reader - Windows Build Script")
    print("=" * 50)
    
    # Check if required tools are available
    try:
        import PyInstaller
        print("[OK] PyInstaller found")
    except ImportError:
        print("[ERROR] PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Create app icon
    create_app_icon()
    
    # Build executable
    if build_windows_executable():
        print("\nBuild completed successfully!")
        
        # Create NSIS installer script
        create_nsis_installer()
        
        print("\nNext steps:")
        print("1. Test the executable in build/windows/installer/")
        print("2. Install NSIS and run: makensis build/windows/installer/installer.nsi")
        print("3. The installer will be created as ECU_BIN_Reader_Setup.exe")
        
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 