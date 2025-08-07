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
    
    # Create PKG script
    pkg_script = f"""
#!/bin/bash

# Create PKG for ECU BIN Reader
PKG_NAME="ECU_BIN_Reader_Installer.pkg"

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
            print("Note: Unsigned apps may show 'damaged' warnings on macOS.")
            print("Users can right-click and select 'Open' to bypass this warning.")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Code signing failed: {e}")
        return False
    except Exception as e:
        print(f"Code signing error: {e}")
        return False


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
    print("Note: Replace with a proper .icns file for production")


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
    
    # Create app icon
    create_app_icon()
    
    # Build app bundle
    if build_macos_app():
        print("\nBuild completed successfully!")
        
        # Code sign the app
        codesign_app()
        
        # Create installer scripts
        create_dmg_installer()
        create_pkg_installer()
        
        # Define build directory
        project_root = Path(__file__).parent
        build_dir = project_root / "build" / "macos"
        
        # Create a proper DMG file
        print("\nCreating DMG file...")
        app_bundle = build_dir / "ECU_BIN_Reader"
        
        if app_bundle.exists():
            # Create a proper DMG using hdiutil
            dmg_path = build_dir / "ECU_BIN_Reader.dmg"
            
            try:
                # Create a temporary directory for DMG contents
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Copy app bundle to temp directory
                    app_dest = temp_path / "ECU BIN Reader.app"
                    shutil.copytree(app_bundle, app_dest)
                    print(f"App bundle copied to temp directory: {app_dest}")
                    
                    # Copy additional files if they exist
                    if (project_root / "README.md").exists():
                        shutil.copy2(project_root / "README.md", temp_path)
                        print("README.md copied to DMG")
                    
                    if (project_root / "LICENSE").exists():
                        shutil.copy2(project_root / "LICENSE", temp_path)
                        print("LICENSE copied to DMG")
                    
                    # Create Applications symlink
                    os.symlink("/Applications", temp_path / "Applications")
                    print("Applications symlink created")
                    
                    # Create DMG using hdiutil
                    print(f"Creating DMG from {temp_path} to {dmg_path}")
                    result = subprocess.run([
                        "hdiutil", "create",
                        "-volname", "ECU BIN Reader",
                        "-srcfolder", str(temp_path),
                        "-ov",  # Overwrite if exists
                        "-format", "UDZO",  # Compressed DMG
                        str(dmg_path)
                    ], capture_output=True, text=True, check=True)
                    
                    print("DMG creation command completed")
                    print(f"stdout: {result.stdout}")
                    if result.stderr:
                        print(f"stderr: {result.stderr}")
                    
                    # Verify DMG was created
                    if dmg_path.exists():
                        print(f"DMG file created successfully: {dmg_path}")
                        print(f"DMG file size: {dmg_path.stat().st_size} bytes")
                        
                        # Add quarantine attribute to allow opening
                        try:
                            subprocess.run([
                                "xattr", "-rd", "com.apple.quarantine", str(dmg_path)
                            ], check=True)
                            print("Removed quarantine attribute from DMG")
                        except subprocess.CalledProcessError:
                            print("Could not remove quarantine attribute (this is normal)")
                        
                    else:
                        print("Error: DMG file not found after creation")
                        raise FileNotFoundError("DMG file not created")
                        
            except subprocess.CalledProcessError as e:
                print(f"DMG creation failed: {e}")
                print(f"stdout: {e.stdout}")
                print(f"stderr: {e.stderr}")
                print(f"Return code: {e.returncode}")
                
                # Fallback: create a simple archive
                print("Falling back to archive creation...")
                import tarfile
                archive_path = build_dir / "ECU_BIN_Reader.tar.gz"
                with tarfile.open(archive_path, "w:gz") as tar:
                    tar.add(app_bundle, arcname="ECU_BIN_Reader")
                shutil.copy2(archive_path, dmg_path)
                print(f"Archive created as fallback: {dmg_path}")
                
            except Exception as e:
                print(f"DMG creation error: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback: create a simple archive
                print("Falling back to archive creation...")
                import tarfile
                archive_path = build_dir / "ECU_BIN_Reader.tar.gz"
                with tarfile.open(archive_path, "w:gz") as tar:
                    tar.add(app_bundle, arcname="ECU_BIN_Reader")
                shutil.copy2(archive_path, dmg_path)
                print(f"Archive created as fallback: {dmg_path}")
        else:
            print(f"Error: App bundle not found at {app_bundle}")
            print(f"Files in build directory: {list(build_dir.iterdir())}")
        
        print("\nNext steps:")
        print("1. Test the app bundle in build/macos/ECU_BIN_Reader")
        print("2. DMG file created: build/macos/ECU_BIN_Reader.dmg")
        print("3. To create PKG: cd build/macos/installer && ./create_pkg.sh")
        print("4. For App Store distribution, use Xcode and App Store Connect")
        print("\nNote: If users get 'damaged' warning, they can:")
        print("   - Right-click the app and select 'Open'")
        print("   - Or run: xattr -rd com.apple.quarantine /path/to/app")
        
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 