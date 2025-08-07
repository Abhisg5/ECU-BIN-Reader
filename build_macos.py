#!/usr/bin/env python3
"""
macOS build script for ECU BIN Reader
Creates a standalone app bundle with PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def build_macos_app():
    """Build macOS app bundle using PyInstaller"""
    
    print("Building ECU BIN Reader for macOS...")
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Create build directory
    build_dir = project_root / "build" / "macos"
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # PyInstaller command for macOS
    cmd = [
        "pyinstaller",
        "--onedir",  # Directory-based app bundle
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
    
    try:
        # Run PyInstaller
        print("Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("PyInstaller completed successfully")
        
        # Check if app bundle was created
        app_path = build_dir / "ECU_BIN_Reader"
        if app_path.exists():
            print(f"App bundle created: {app_path}")
            
            # Create installer directory
            installer_dir = build_dir / "installer"
            installer_dir.mkdir(exist_ok=True)
            
            # Copy app bundle to installer directory
            shutil.copytree(app_path, installer_dir / "ECU_BIN_Reader", dirs_exist_ok=True)
            
            # Copy additional files
            if (project_root / "README.md").exists():
                shutil.copy2(project_root / "README.md", installer_dir)
            
            if (project_root / "LICENSE").exists():
                shutil.copy2(project_root / "LICENSE", installer_dir)
            
            # Create shell script for easy execution
            shell_content = """#!/bin/bash
echo "Starting ECU BIN Reader..."
./ECU_BIN_Reader/ECU_BIN_Reader
"""
            shell_script = installer_dir / "run.sh"
            with open(shell_script, "w") as f:
                f.write(shell_content)
            
            # Make shell script executable
            os.chmod(shell_script, 0o755)
            
            print(f"Installer package created in: {installer_dir}")
            
        else:
            print("Error: App bundle not found")
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


def create_dmg_installer():
    """Create DMG installer"""
    
    build_dir = Path(__file__).parent / "build" / "macos" / "installer"
    
    # Create DMG script
    dmg_script = f"""
#!/bin/bash

# Create DMG for ECU BIN Reader
APP_NAME="ECU BIN Reader"
DMG_NAME="ECU_BIN_Reader_1.0.0.dmg"
VOLUME_NAME="ECU BIN Reader"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
APP_DIR="$TEMP_DIR/$APP_NAME.app"

# Copy app bundle
if [ -d "{build_dir}/ECU_BIN_Reader" ]; then
    cp -R "{build_dir}/ECU_BIN_Reader" "$APP_DIR"
    echo "App bundle copied successfully"
else
    echo "Error: App bundle not found at {build_dir}/ECU_BIN_Reader"
    exit 1
fi

# Copy additional files (if they exist)
if [ -f "{build_dir}/README.md" ]; then
    cp "{build_dir}/README.md" "$TEMP_DIR/"
    echo "README.md copied"
fi

if [ -f "{build_dir}/LICENSE" ]; then
    cp "{build_dir}/LICENSE" "$TEMP_DIR/"
    echo "LICENSE copied"
fi

# Create Applications symlink
ln -s /Applications "$TEMP_DIR/Applications"

# Create DMG
echo "Creating DMG file..."
hdiutil create -volname "$VOLUME_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_NAME"

# Check if DMG was created
if [ -f "$DMG_NAME" ]; then
    echo "DMG created successfully: $DMG_NAME"
else
    echo "Error: DMG creation failed"
    exit 1
fi

# Clean up
rm -rf "$TEMP_DIR"

echo "DMG creation completed: $DMG_NAME"
"""
    
    dmg_script_path = build_dir / "create_dmg.sh"
    with open(dmg_script_path, "w") as f:
        f.write(dmg_script)
    
    # Make script executable
    os.chmod(dmg_script_path, 0o755)
    
    print(f"DMG creation script created: {dmg_script_path}")
    print("To create DMG, run: ./create_dmg.sh")


def create_pkg_installer():
    """Create PKG installer using pkgbuild"""
    
    build_dir = Path(__file__).parent / "build" / "macos" / "installer"
    
    # Create component plist
    component_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<array>
    <dict>
        <key>BundleHasStrictIdentifier</key>
        <true/>
        <key>BundleIsRelocatable</key>
        <false/>
        <key>BundleIsVersionChecked</key>
        <true/>
        <key>BundleOverwriteAction</key>
        <string>upgrade</string>
        <key>RootRelativeBundlePath</key>
        <string>ECU_BIN_Reader.app</string>
    </dict>
</array>
</plist>
"""
    
    component_plist_path = build_dir / "component.plist"
    with open(component_plist_path, "w") as f:
        f.write(component_plist)
    
    # Create distribution plist
    distribution_plist = """<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>ECU BIN Reader</title>
    <organization>com.ecutools.ecubinreader</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="true"/>
    <pkg-ref id="com.ecutools.ecubinreader"/>
    <choices-outline>
        <line choice="com.ecutools.ecubinreader"/>
    </choices-outline>
    <choice id="com.ecutools.ecubinreader" title="ECU BIN Reader">
        <pkg-ref id="com.ecutools.ecubinreader"/>
    </choice>
    <pkg-ref id="com.ecutools.ecubinreader" version="1.0.0" onConclusion="none">ECU_BIN_Reader.pkg</pkg-ref>
</installer-gui-script>
"""
    
    distribution_plist_path = build_dir / "distribution.plist"
    with open(distribution_plist_path, "w") as f:
        f.write(distribution_plist)
    
    # Create PKG build script
    pkg_script = f"""
#!/bin/bash

# Create PKG installer for ECU BIN Reader
APP_NAME="ECU BIN Reader"
PKG_NAME="ECU_BIN_Reader.pkg"
COMPONENT_PLIST="{component_plist_path}"
DISTRIBUTION_PLIST="{distribution_plist_path}"

# Build component package
pkgbuild --component "{build_dir}/ECU_BIN_Reader" \\
         --install-location "/Applications" \\
         --identifier "com.ecutools.ecubinreader" \\
         --version "1.0.0" \\
         --root "{build_dir}" \\
         "$PKG_NAME"

# Build distribution package
productbuild --distribution "$DISTRIBUTION_PLIST" \\
            --package-path "." \\
            --resources "." \\
            "ECU_BIN_Reader_Installer.pkg"

echo "PKG created: ECU_BIN_Reader_Installer.pkg"
"""
    
    pkg_script_path = build_dir / "create_pkg.sh"
    with open(pkg_script_path, "w") as f:
        f.write(pkg_script)
    
    # Make script executable
    os.chmod(pkg_script_path, 0o755)
    
    print(f"PKG creation script created: {pkg_script_path}")
    print("To create PKG, run: ./create_pkg.sh")


def codesign_app():
    """Code sign the app bundle (if certificate is available)"""
    
    build_dir = Path(__file__).parent / "build" / "macos" / "installer"
    app_path = build_dir / "ECU_BIN_Reader"
    
    if not app_path.exists():
        print("App bundle not found for code signing")
        return False
    
    try:
        # Check if we have a certificate
        result = subprocess.run(["security", "find-identity", "-v", "-p", "codesigning"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and "Developer ID Application" in result.stdout:
            print("Code signing app bundle...")
            
            # Code sign the app
            subprocess.run([
                "codesign", "--force", "--deep", "--sign", "Developer ID Application",
                str(app_path)
            ], check=True)
            
            print("App bundle code signed successfully")
            return True
        else:
            print("No code signing certificate found. App will be unsigned.")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Code signing failed: {e}")
        return False
    except Exception as e:
        print(f"Code signing error: {e}")
        return False


def main():
    """Main build function"""
    
    print("ECU BIN Reader - macOS Build Script")
    print("=" * 50)
    
    # Check if required tools are available
    try:
        import PyInstaller
        print("[OK] PyInstaller found")
    except ImportError:
        print("[ERROR] PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build app bundle
    if build_macos_app():
        print("\nBuild completed successfully!")
        
        # Define build directory
        project_root = Path(__file__).parent
        build_dir = project_root / "build" / "macos"
        
        # Code sign the app
        codesign_app()
        
        # Create installer scripts
        create_dmg_installer()
        create_pkg_installer()
        
        # Actually create the DMG file
        print("\nCreating DMG file...")
        installer_dir = build_dir / "installer"
        dmg_script = installer_dir / "create_dmg.sh"
        
        if dmg_script.exists():
            try:
                print(f"Running DMG creation script from: {installer_dir}")
                print(f"DMG script path: {dmg_script}")
                
                # Run the DMG creation script
                result = subprocess.run(["./create_dmg.sh"], 
                                     cwd=installer_dir, 
                                     check=True, 
                                     capture_output=True, 
                                     text=True)
                print("DMG file created successfully!")
                print(f"Script output: {result.stdout}")
                
                # Check if DMG was created
                dmg_file = installer_dir / "ECU_BIN_Reader_1.0.0.dmg"
                if dmg_file.exists():
                    # Copy DMG to build directory for GitHub Actions
                    final_dmg = build_dir / "ECU_BIN_Reader.dmg"
                    shutil.copy2(dmg_file, final_dmg)
                    print(f"DMG file ready: {final_dmg}")
                    print(f"DMG file size: {final_dmg.stat().st_size} bytes")
                else:
                    print("Warning: DMG file not found after creation")
                    print(f"Looking for: {dmg_file}")
                    print(f"Files in installer directory: {list(installer_dir.iterdir())}")
                    
            except subprocess.CalledProcessError as e:
                print(f"DMG creation failed: {e}")
                print(f"stdout: {e.stdout}")
                print(f"stderr: {e.stderr}")
                print(f"Return code: {e.returncode}")
            except Exception as e:
                print(f"DMG creation error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"DMG script not found at: {dmg_script}")
            print(f"Files in installer directory: {list(installer_dir.iterdir())}")
        
        print("\nNext steps:")
        print("1. Test the app bundle in build/macos/installer/ECU_BIN_Reader")
        print("2. DMG file created: build/macos/ECU_BIN_Reader.dmg")
        print("3. To create PKG: cd build/macos/installer && ./create_pkg.sh")
        print("4. For App Store distribution, use Xcode and App Store Connect")
        
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 