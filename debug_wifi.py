#!/usr/bin/env python3
"""
Debug script to test WiFi connection specifically for Gateway_F46F93
"""

import asyncio
import subprocess
from colorama import init, Fore, Style

# Initialize colorama
init()

async def test_gateway_connection():
    """Test connecting to Gateway_F46F93"""
    ssid = "Gateway_F46F93"
    
    print(f"{Fore.CYAN}🧪 Testing connection to {ssid}{Style.RESET_ALL}")
    
    # First, let's see the current WiFi status
    print(f"\n{Fore.BLUE}📊 Current WiFi status:{Style.RESET_ALL}")
    result = subprocess.run(["networksetup", "-getairportnetwork", "en0"], 
                          capture_output=True, text=True)
    print(f"Current network: {result.stdout.strip()}")
    
    # Try to connect (this will likely fail without password for secured networks)
    print(f"\n{Fore.YELLOW}🔌 Attempting connection without password:{Style.RESET_ALL}")
    cmd = ["networksetup", "-setairportnetwork", "en0", ssid]
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout.strip()}")
    print(f"Stderr: {result.stderr.strip()}")
    
    # Check if we're connected
    await asyncio.sleep(2)
    result = subprocess.run(["networksetup", "-getairportnetwork", "en0"], 
                          capture_output=True, text=True)
    print(f"\nAfter connection attempt: {result.stdout.strip()}")
    
    # Test if we can reach the gateway IP
    print(f"\n{Fore.BLUE}🌐 Testing connectivity to 192.168.1.1:{Style.RESET_ALL}")
    ping_result = subprocess.run(["ping", "-c", "1", "-W", "3000", "192.168.1.1"], 
                               capture_output=True, text=True)
    if ping_result.returncode == 0:
        print(f"{Fore.GREEN}✅ Can reach 192.168.1.1{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Cannot reach 192.168.1.1{Style.RESET_ALL}")
        print(f"Ping output: {ping_result.stdout.strip()}")

if __name__ == "__main__":
    asyncio.run(test_gateway_connection())
