#!/usr/bin/env python3
"""
Test script to verify the UG63 Gateway Configuration Bot setup
"""

import asyncio
import sys
import platform
from colorama import init, Fore, Style

# Initialize colorama
init()

async def test_imports():
    """Test if all required modules can be imported"""
    from colorama import Fore, Style
    print(f"{Fore.BLUE}📦 Testing imports...{Style.RESET_ALL}")
    
    try:
        from playwright.async_api import async_playwright
        print(f"  {Fore.GREEN}✅ Playwright imported successfully{Style.RESET_ALL}")
        
        import click
        print(f"  {Fore.GREEN}✅ Click imported successfully{Style.RESET_ALL}")
        
        from colorama import init
        print(f"  {Fore.GREEN}✅ Colorama imported successfully{Style.RESET_ALL}")
        
        import subprocess
        print(f"  {Fore.GREEN}✅ Subprocess available{Style.RESET_ALL}")
        
        return True
    except ImportError as e:
        print(f"  {Fore.RED}❌ Import failed: {e}{Style.RESET_ALL}")
        return False

async def test_playwright():
    """Test if Playwright browsers are installed"""
    from colorama import Fore, Style
    print(f"\n{Fore.BLUE}🌐 Testing Playwright browser...{Style.RESET_ALL}")
    
    try:
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("about:blank")
        await browser.close()
        await playwright.stop()
        
        print(f"  {Fore.GREEN}✅ Playwright Chromium browser working{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"  {Fore.RED}❌ Playwright test failed: {e}{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}💡 Try running: uv run playwright install chromium{Style.RESET_ALL}")
        return False

def test_wifi_commands():
    """Test if WiFi commands are available"""
    from colorama import Fore, Style
    import subprocess
    
    print(f"\n{Fore.BLUE}📶 Testing WiFi commands...{Style.RESET_ALL}")
    
    system = platform.system()
    success = True
    
    if system == "Darwin":  # macOS
        try:
            subprocess.run([
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                "--help"
            ], capture_output=True, timeout=5)
            print(f"  {Fore.GREEN}✅ macOS airport command available{Style.RESET_ALL}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  {Fore.YELLOW}⚠️ macOS airport command not found or timeout{Style.RESET_ALL}")
            success = False
            
        try:
            subprocess.run(["networksetup", "-help"], capture_output=True, timeout=5)
            print(f"  {Fore.GREEN}✅ macOS networksetup command available{Style.RESET_ALL}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  {Fore.RED}❌ macOS networksetup command not found{Style.RESET_ALL}")
            success = False
            
    elif system == "Linux":
        try:
            subprocess.run(["nmcli", "--version"], capture_output=True, timeout=5)
            print(f"  {Fore.GREEN}✅ Linux nmcli command available{Style.RESET_ALL}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  {Fore.RED}❌ Linux nmcli command not found{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}💡 Install NetworkManager: sudo apt-get install network-manager{Style.RESET_ALL}")
            success = False
            
        try:
            subprocess.run(["iwlist", "--version"], capture_output=True, timeout=5)
            print(f"  {Fore.GREEN}✅ Linux iwlist command available{Style.RESET_ALL}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  {Fore.YELLOW}⚠️ Linux iwlist command not found (optional){Style.RESET_ALL}")
            
    elif system == "Windows":
        try:
            subprocess.run(["netsh", "wlan", "show", "help"], capture_output=True, timeout=5)
            print(f"  {Fore.GREEN}✅ Windows netsh command available{Style.RESET_ALL}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  {Fore.RED}❌ Windows netsh command not found{Style.RESET_ALL}")
            success = False
    
    return success

def test_permissions():
    """Test if we have necessary permissions"""
    from colorama import Fore, Style
    import os
    
    print(f"\n{Fore.BLUE}🔐 Testing permissions...{Style.RESET_ALL}")
    
    system = platform.system()
    
    if system == "Darwin":
        print(f"  {Fore.YELLOW}⚠️ macOS: May need sudo for WiFi operations{Style.RESET_ALL}")
        print(f"  {Fore.BLUE}💡 Test with: sudo uv run python gateway_config_bot.py{Style.RESET_ALL}")
        
    elif system == "Linux":
        if os.geteuid() == 0:
            print(f"  {Fore.GREEN}✅ Running with root privileges{Style.RESET_ALL}")
        else:
            print(f"  {Fore.YELLOW}⚠️ Not running as root - may need sudo for WiFi{Style.RESET_ALL}")
            
    elif system == "Windows":
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            print(f"  {Fore.GREEN}✅ Running with administrator privileges{Style.RESET_ALL}")
        else:
            print(f"  {Fore.YELLOW}⚠️ Not running as administrator - may need elevated privileges{Style.RESET_ALL}")
    
    return True

async def main():
    """Main test function"""
    print(f"{Fore.CYAN}🧪 UG63 Gateway Bot Setup Test{Style.RESET_ALL}")
    print(f"{Fore.CYAN}================================{Style.RESET_ALL}")
    
    print(f"{Fore.BLUE}🖥️ System: {platform.system()} {platform.release()}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}🐍 Python: {sys.version.split()[0]}{Style.RESET_ALL}")
    
    tests = [
        ("Imports", test_imports()),
        ("Playwright", test_playwright()),
        ("WiFi Commands", test_wifi_commands()),
        ("Permissions", test_permissions())
    ]
    
    results = []
    for test_name, test_coro in tests:
        if asyncio.iscoroutine(test_coro):
            result = await test_coro
        else:
            result = test_coro
        results.append(result)
    
    # Summary
    print(f"\n{Fore.CYAN}📊 Test Summary:{Style.RESET_ALL}")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{Fore.GREEN}🎉 All tests passed! ({passed}/{total}){Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}✅ Setup is ready - you can run the bot!{Style.RESET_ALL}")
        print(f"{Fore.BLUE}🚀 Run: python gateway_config_bot.py{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️ {passed}/{total} tests passed{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Please fix the issues above before running the bot.{Style.RESET_ALL}")
        
        if passed >= 2:  # Core functionality works
            print(f"{Fore.BLUE}💡 You may still be able to run the bot with some limitations.{Style.RESET_ALL}")

def cli_main():
    """CLI entry point for uv scripts"""
    asyncio.run(main())

if __name__ == "__main__":
    cli_main()
