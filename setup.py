#!/usr/bin/env python3
"""
Setup script for UG63 Gateway Configuration Bot
"""

import subprocess
import sys
import platform
import os

def install_python_dependencies():
    """Install Python dependencies using uv"""
    print("📦 Installing Python dependencies with uv...")
    try:
        # Try uv first
        subprocess.check_call(["uv", "sync"])
        print("  ✅ Dependencies installed with uv")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ⚠️ uv not found, falling back to pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", ".", "-v"])
            print("  ✅ Dependencies installed with pip")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install with pip: {e}")
            raise

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("🌐 Installing Playwright browsers...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def setup_permissions():
    """Setup necessary permissions for WiFi management"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        print("🍎 macOS detected")
        print("⚠️  You may need to run with sudo for WiFi operations")
        print("💡 Alternative: Add your user to admin group and allow airport utility")
        
    elif system == "Linux":
        print("🐧 Linux detected")
        print("📝 Make sure NetworkManager is installed and running")
        print("💡 You may need to run with sudo or add your user to netdev group")
        
    elif system == "Windows":
        print("🪟 Windows detected")
        print("⚠️  Run as administrator for WiFi operations")
        
def main():
    """Main setup function"""
    print("🤖 UG63 Gateway Configuration Bot Setup")
    print("=" * 40)
    
    try:
        install_python_dependencies()
        install_playwright_browsers()
        setup_permissions()
        
        print("\n✅ Setup completed successfully!")
        print("\n🚀 You can now run the bot with:")
        print("   python gateway_config_bot.py")
        print("\n💡 For help, use:")
        print("   python gateway_config_bot.py --help")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
