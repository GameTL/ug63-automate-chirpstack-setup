#!/usr/bin/env python3
"""
UG63 LoRaWAN Gateway Configuration Bot

This bot automates the configuration of multiple UG63 gateways by:
1. Scanning for Gateway_* WiFi networks
2. Connecting to selected gateways
3. Automating browser-based configuration
"""

import asyncio
import time
import sys
from typing import List, Dict, Optional
import click
from colorama import init, Fore, Style
from playwright.async_api import async_playwright, Page, Browser
import subprocess
import json
import platform
import yaml
from pathlib import Path

# Initialize colorama for cross-platform colored output
init()

class ConfigLoader:
    """Handles loading and accessing configuration from config.yaml"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                print(f"{Fore.RED}❌ Config file not found: {self.config_path}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Please ensure config.yaml exists in the project directory{Style.RESET_ALL}")
                sys.exit(1)
            
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            print(f"{Fore.GREEN}✅ Configuration loaded from {self.config_path}{Style.RESET_ALL}")
            return config
            
        except yaml.YAMLError as e:
            print(f"{Fore.RED}❌ Error parsing config file: {e}{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading config file: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'credentials.default_username')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value

class WiFiManager:
    """Handles WiFi scanning and connection operations"""
    
    def __init__(self):
        self.system = platform.system()
    
    async def scan_gateway_networks(self) -> List[Dict[str, str]]:
        """Scan for WiFi networks starting with 'Gateway_'"""
        print(f"{Fore.BLUE}🔍 Scanning for Gateway WiFi networks...{Style.RESET_ALL}")
        
        try:
            if self.system == "Darwin":  # macOS
                # Use system_profiler instead of deprecated airport command
                result = subprocess.run([
                    "system_profiler", "SPAirPortDataType"
                ], capture_output=True, text=True)
                
                networks = []
                in_networks_section = False
                current_network = None
                
                for line in result.stdout.split('\n'):
                    line_stripped = line.strip()
                    
                    # Look for "Other Local Wi-Fi Networks:" section
                    if "Other Local Wi-Fi Networks:" in line:
                        in_networks_section = True
                        continue
                    
                    if not in_networks_section:
                        continue
                    
                    # Check if this is a network name (ends with colon and contains Gateway_)
                    if line_stripped.endswith(':') and 'Gateway_' in line_stripped:
                        # If we have a pending network without security info, add it with default
                        if current_network:
                            current_network["security"] = "Unknown"
                            networks.append(current_network)
                        
                        # Extract SSID (remove the trailing colon)
                        ssid = line_stripped[:-1]
                        current_network = {
                            "ssid": ssid,
                            "signal": "Unknown",
                            "security": "Unknown"
                        }
                        continue
                    
                    # Parse security information for current network
                    if current_network and "Security:" in line:
                        security_info = line.split("Security:", 1)[1].strip()
                        current_network["security"] = security_info
                        # Add the completed network to our list
                        networks.append(current_network)
                        current_network = None
                
                # Don't forget the last network if it didn't have security info
                if current_network:
                    current_network["security"] = "Unknown"
                    networks.append(current_network)
                
            elif self.system == "Linux":
                result = subprocess.run(["iwlist", "scan"], capture_output=True, text=True)
                # Parse iwlist output for Gateway_ networks
                networks = self._parse_iwlist_output(result.stdout)
                
            else:  # Windows
                result = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True)
                networks = self._parse_netsh_output(result.stdout)
            
            return networks
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error scanning WiFi networks: {e}{Style.RESET_ALL}")
            return []
    
    def _parse_iwlist_output(self, output: str) -> List[Dict[str, str]]:
        """Parse iwlist scan output for Gateway_ networks"""
        networks = []
        current_network = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if 'ESSID:' in line and 'Gateway_' in line:
                ssid = line.split('"')[1] if '"' in line else line.split(':')[1]
                current_network['ssid'] = ssid
                current_network['signal'] = "Unknown"
                current_network['security'] = "Unknown"
                networks.append(current_network)
                current_network = {}
        
        return networks
    
    def _parse_netsh_output(self, output: str) -> List[Dict[str, str]]:
        """Parse netsh output for Gateway_ networks"""
        networks = []
        for line in output.split('\n'):
            if 'Gateway_' in line:
                ssid = line.split(':')[1].strip() if ':' in line else line.strip()
                networks.append({
                    "ssid": ssid,
                    "signal": "Unknown",
                    "security": "Unknown"
                })
        return networks
    
    async def connect_to_network(self, ssid: str, password: Optional[str] = None) -> bool:
        """Connect to a WiFi network"""
        print(f"{Fore.YELLOW}📶 Connecting to {ssid}...{Style.RESET_ALL}")
        
        try:
            if self.system == "Darwin":  # macOS
                if password:
                    cmd = ["networksetup", "-setairportnetwork", "en0", ssid, password]
                else:
                    cmd = ["networksetup", "-setairportnetwork", "en0", ssid]
                
            elif self.system == "Linux":
                if password:
                    cmd = ["nmcli", "dev", "wifi", "connect", ssid, "password", password]
                else:
                    cmd = ["nmcli", "dev", "wifi", "connect", ssid]
                    
            else:  # Windows
                if password:
                    cmd = ["netsh", "wlan", "connect", f"ssid={ssid}", f"key={password}"]
                else:
                    cmd = ["netsh", "wlan", "connect", f"ssid={ssid}"]
            
            print(f"{Fore.CYAN}🔧 Running: {' '.join(cmd)}{Style.RESET_ALL}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            print(f"{Fore.CYAN}📤 Command output: {result.stdout.strip()}{Style.RESET_ALL}")
            if result.stderr.strip():
                print(f"{Fore.YELLOW}⚠️ Command stderr: {result.stderr.strip()}{Style.RESET_ALL}")
            
            if result.returncode == 0:
                print(f"{Fore.GREEN}✅ Successfully connected to {ssid}{Style.RESET_ALL}")
                await asyncio.sleep(5)  # Wait for connection to stabilize
                return True
            else:
                print(f"{Fore.RED}❌ Failed to connect to {ssid} (exit code: {result.returncode}){Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error connecting to {ssid}: {e}{Style.RESET_ALL}")
            return False

class GatewayConfigBot:
    """Main bot class for configuring UG63 gateways"""
    
    def __init__(self, interactive_mode: bool = False, config_path: str = "config.yaml"):
        self.wifi_manager = WiFiManager()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.interactive_mode = interactive_mode
        self.config = ConfigLoader(config_path)
        
    async def initialize_browser(self):
        """Initialize the browser instance"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        
    async def close_browser(self):
        """Close the browser instance"""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
                self.page = None
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Error closing browser: {e}{Style.RESET_ALL}")
    
    def pause_for_manual_work(self, step_name: str, description: str) -> str:
        """Pause execution and ask user what to do next"""
        if not self.interactive_mode:
            return "continue"
            
        print(f"\n{Fore.MAGENTA}⏸️  PAUSE: {step_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📋 {description}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Options:{Style.RESET_ALL}")
        print("• 'c' or 'continue' - Continue with automation")
        print("• 'p' or 'pause' - Pause here (you handle this step manually)")
        print("• 's' or 'skip' - Skip this step entirely")
        print("• 'q' or 'quit' - Quit the bot")
        
        while True:
            choice = input(f"{Fore.YELLOW}What would you like to do? {Style.RESET_ALL}").strip().lower()
            
            if choice in ['c', 'continue']:
                print(f"{Fore.GREEN}▶️ Continuing with automation...{Style.RESET_ALL}")
                return "continue"
            elif choice in ['p', 'pause']:
                print(f"{Fore.BLUE}⏸️ Pausing for manual work. Press Enter when you're done...{Style.RESET_ALL}")
                input()
                print(f"{Fore.GREEN}▶️ Resuming automation...{Style.RESET_ALL}")
                return "manual_done"
            elif choice in ['s', 'skip']:
                print(f"{Fore.YELLOW}⏭️ Skipping this step...{Style.RESET_ALL}")
                return "skip"
            elif choice in ['q', 'quit']:
                print(f"{Fore.RED}🛑 Quitting bot...{Style.RESET_ALL}")
                return "quit"
            else:
                print(f"{Fore.RED}❌ Invalid choice. Please enter 'c', 'p', 's', or 'q'{Style.RESET_ALL}")
    
    async def wait_for_element(self, selector: str, timeout: int = 10000) -> bool:
        """Wait for an element to be present and visible"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Element not found: {selector} - {e}{Style.RESET_ALL}")
            return False
    
    async def login_to_gateway(self, username: str = "admin", password: str = "password") -> bool:
        """Login to the gateway web interface"""
        print(f"{Fore.BLUE}🔐 Logging into gateway...{Style.RESET_ALL}")
        
        # Use config values if not provided
        username = username or self.config.get('credentials.default_username', 'admin')
        password = password or self.config.get('credentials.default_password', 'password')
        gateway_ip = self.config.get('web_interface.ip_address', '192.168.1.1')
        protocol = self.config.get('web_interface.protocol', 'http')
        
        try:
            # Navigate to gateway IP
            gateway_url = f"{protocol}://{gateway_ip}"
            await self.page.goto(gateway_url, timeout=30000)
            
            # Wait for login form
            if not await self.wait_for_element('#username'):
                return False
            
            # Fill username
            await self.page.fill('#username', username)
            
            # Fill password
            await self.page.fill('#password', password)
            
            # Click login button
            await self.page.click('button.ui-button:has-text("Login")')
            
            # Wait for page load after login
            await asyncio.sleep(3)
            
            print(f"{Fore.GREEN}✅ Successfully logged in{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Login failed: {e}{Style.RESET_ALL}")
            return False
    
    async def configure_chirpstack(self) -> bool:
        """Configure ChirpStack settings"""
        print(f"{Fore.BLUE}⚙️ Configuring ChirpStack...{Style.RESET_ALL}")
        
        # Get configuration values
        server_address = self.config.get('chirpstack.server_address', '192.168.1.1')
        server_port = str(self.config.get('chirpstack.server_port', 1884))
        protocol = self.config.get('chirpstack.protocol', 'ChirpStack-v4')
        
        try:
            # Click Packet Forward
            await self.page.click('a[href="packet"]')
            await asyncio.sleep(2)
            
            # Click dropdown menu
            dropdown_selector = '.ui-select-button:has-text("Embedded NS")'
            await self.page.click(dropdown_selector)
            await asyncio.sleep(1)
            
            # Select ChirpStack protocol
            await self.page.click(f'a.ui-select-datalist-li:has-text("{protocol}")')
            await asyncio.sleep(1)
            
            # Fill address
            await self.page.fill('#cs4_address', server_address)
            
            # Fill port
            await self.page.fill('input[name="cs4_port"]', server_port)
            
            # Click Save & Apply
            await self.page.click('button:has-text("Save & Apply")')
            
            # Wait for save to complete
            await asyncio.sleep(10)
            
            print(f"{Fore.GREEN}✅ ChirpStack configuration saved{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📡 Server: {server_address}:{server_port} ({protocol}){Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ ChirpStack configuration failed: {e}{Style.RESET_ALL}")
            return False
    
    async def change_password(self, old_password: str = "password", new_password: str = "password") -> bool:
        """Change the admin password"""
        print(f"{Fore.BLUE}🔑 Changing admin password...{Style.RESET_ALL}")
        
        # Use config values if not provided
        old_password = old_password or self.config.get('credentials.default_password', 'password')
        new_password = new_password or self.config.get('credentials.new_password')
        
        if not new_password:
            print(f"{Fore.RED}❌ New password not configured. Please set 'credentials.new_password' in config.yaml{Style.RESET_ALL}")
            return False
        
        try:
            # Click System
            await self.page.click('a[href="system"]')
            await asyncio.sleep(2)
            
            # Click User
            await self.page.click('a[href="/system/general"]:has-text("User")')
            await asyncio.sleep(2)
            
            # Fill old password
            await self.page.fill('#old_pwd', old_password)
            
            # Fill new password
            await self.page.fill('#new_pwd', new_password)
            
            # Fill confirm password
            await self.page.fill('#check_pwd', new_password)
            
            # Click Save & Apply
            await self.page.click('button:has-text("Save & Apply")')
            
            # Wait for save to complete
            await asyncio.sleep(3)
            
            print(f"{Fore.GREEN}✅ Password changed successfully{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Password change failed: {e}{Style.RESET_ALL}")
            return False
    
    async def relogin_with_new_password(self, username: str = "admin", password: str = "password") -> bool:
        """Re-login with the new password after password change"""
        print(f"{Fore.BLUE}🔐 Re-logging in with new password...{Style.RESET_ALL}")
        
        # Use config values if not provided
        username = username or self.config.get('credentials.new_username', 'admin')
        password = password or self.config.get('credentials.new_password')
        
        if not password:
            print(f"{Fore.RED}❌ New password not configured. Please set 'credentials.new_password' in config.yaml{Style.RESET_ALL}")
            return False
        
        try:
            # Wait for redirect to login page
            await asyncio.sleep(2)
            
            # Fill username
            await self.page.fill('#username', username)
            
            # Fill new password
            await self.page.fill('#password', password)
            
            # Click login
            await self.page.click('button:has-text("Login")')
            
            # Wait for login
            await asyncio.sleep(3)
            
            print(f"{Fore.GREEN}✅ Re-login successful{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Re-login failed: {e}{Style.RESET_ALL}")
            return False
    
    async def configure_network(self) -> bool:
        """Configure network settings to use Cellular"""
        print(f"{Fore.BLUE}📡 Configuring network settings...{Style.RESET_ALL}")
        
        try:
            # Click Network
            await self.page.click('a[href="network"]')
            await asyncio.sleep(2)
            
            # Click dropdown for WAN - be more specific with the selector
            dropdown_selector = '.ui-select-button'
            await self.page.click(dropdown_selector)
            await asyncio.sleep(2)  # Give more time for dropdown to open
            
            # Select Cellular - use a more specific selector that targets non-selected items
            cellular_selector = 'a.ui-select-datalist-li[aria-selected="false"]:has-text("Cellular")'
            
            # If that doesn't work, try a more general approach
            cellular_elements = await self.page.locator('a.ui-select-datalist-li:has-text("Cellular")').all()
            print(f"{Fore.CYAN}📡 Debug: Found {len(cellular_elements)} Cellular elements{Style.RESET_ALL}")
            
            clicked = False
            for i, element in enumerate(cellular_elements):
                try:
                    # Check if element is visible and not already selected
                    is_visible = await element.is_visible()
                    aria_selected = await element.get_attribute('aria-selected')
                    print(f"{Fore.CYAN}📡 Debug: Element {i}: visible={is_visible}, selected={aria_selected}{Style.RESET_ALL}")
                    
                    if is_visible and aria_selected == "false":
                        await element.click()
                        clicked = True
                        print(f"{Fore.GREEN}✅ Successfully clicked Cellular option {i}{Style.RESET_ALL}")
                        break
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Failed to click element {i}: {e}{Style.RESET_ALL}")
                    continue
            
            if not clicked:
                print(f"{Fore.RED}❌ Could not find clickable Cellular option{Style.RESET_ALL}")
                return False
            
            await asyncio.sleep(1)
            
            # Click Save & Apply
            await self.page.click('button:has-text("Save & Apply")')
            await asyncio.sleep(5)
            
            print(f"{Fore.GREEN}✅ Network configured to use Cellular{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Network configuration failed: {e}{Style.RESET_ALL}")
            return False
    
    async def configure_wifi_password(self, wifi_password: str = "password") -> bool:
        """Configure WiFi password"""
        print(f"{Fore.BLUE}📶 Configuring WiFi password...{Style.RESET_ALL}")
        
        # Use config value if not provided
        wifi_password = wifi_password or self.config.get('wifi.password')
        encryption = self.config.get('wifi.encryption', 'WPA-PSK')
        
        if not wifi_password:
            print(f"{Fore.RED}❌ WiFi password not configured. Please set 'wifi.password' in config.yaml{Style.RESET_ALL}")
            return False
        
        try:
            # Click WLAN
            await self.page.click('a[href="/network/wlan"]:has-text("WLAN")')
            await asyncio.sleep(2)
            
            # Click dropdown for encryption
            dropdown_selector = '.ui-select-button:has-text("No Encryption")'
            await self.page.click(dropdown_selector)
            await asyncio.sleep(1)
            
            # Select encryption type
            await self.page.click(f'a.ui-select-datalist-li:has-text("{encryption}")')
            await asyncio.sleep(1)
            
            # Fill WiFi password
            await self.page.fill('#ap_pwd', wifi_password)
            
            # Click Save & Apply
            await self.page.click('button:has-text("Save & Apply")')
            await asyncio.sleep(5)
            
            print(f"{Fore.GREEN}✅ WiFi password configured{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🔐 Encryption: {encryption}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ WiFi password configuration failed: {e}{Style.RESET_ALL}")
            return False
    
    async def configure_single_gateway(self, ssid: str, max_retries: int = 2, start_from_step: int = 1) -> bool:
        """Configure a single gateway through the complete process"""
        print(f"\n{Fore.CYAN}🚀 Starting configuration for {ssid}{Style.RESET_ALL}")
        if start_from_step > 1:
            print(f"{Fore.BLUE}📍 Resuming from step {start_from_step}{Style.RESET_ALL}")
        
        steps = [
            (1, "WiFi Connection", "Connect to gateway WiFi network"),
            (2, "Browser & Login", "Open browser and login to gateway web interface"),
            (3, "ChirpStack Config", "Configure ChirpStack v4 settings"),
            (4, "Password Change", "Change admin password for security"),
            (5, "Re-login", "Re-login with new password"),
            (6, "Network Config", "Configure network settings (Cellular)"),
            (7, "WiFi Security", "Configure WiFi password and security")
        ]
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"{Fore.YELLOW}🔄 Retry attempt {attempt}/{max_retries} for {ssid}{Style.RESET_ALL}")
                    await asyncio.sleep(5)  # Wait before retry
                
                # Step 1: Connect to WiFi
                if start_from_step <= 1:
                    action = self.pause_for_manual_work("Step 1: WiFi Connection", 
                                                      f"About to connect to {ssid}")
                    if action == "quit":
                        return False
                    elif action == "continue":
                        if not await self.wifi_manager.connect_to_network(ssid):
                            if attempt < max_retries:
                                continue
                            return False
                    elif action == "skip":
                        print(f"{Fore.BLUE}⚠️ Assuming you're already connected to {ssid}{Style.RESET_ALL}")
                
                # Initialize browser
                if start_from_step <= 2:
                    await self.initialize_browser()
                
                # Step 2: Login
                if start_from_step <= 2:
                    gateway_ip = self.config.get('web_interface.ip_address', '192.168.1.1')
                    action = self.pause_for_manual_work("Step 2: Login", 
                                                      f"About to login to gateway ({gateway_ip})")
                    if action == "quit":
                        await self.close_browser()
                        return False
                    elif action == "continue":
                        if not await self.login_to_gateway():
                            await self.close_browser()
                            if attempt < max_retries:
                                continue
                            return False
                    elif action == "skip":
                        print(f"{Fore.BLUE}⚠️ Assuming you're already logged in{Style.RESET_ALL}")
                
                # Step 3: Configure ChirpStack
                if start_from_step <= 3:
                    server_address = self.config.get('chirpstack.server_address', '192.168.1.1')
                    server_port = self.config.get('chirpstack.server_port', 1883)
                    action = self.pause_for_manual_work("Step 3: ChirpStack", 
                                                      f"About to configure ChirpStack v4 ({server_address}:{server_port})")
                    if action == "quit":
                        await self.close_browser()
                        return False
                    elif action == "continue":
                        if not await self.configure_chirpstack():
                            await self.close_browser()
                            if attempt < max_retries:
                                continue
                            return False
                    elif action == "skip":
                        print(f"{Fore.BLUE}⚠️ Skipping ChirpStack configuration{Style.RESET_ALL}")
                
                # Step 4: Change password
                if start_from_step <= 4:
                    new_password = self.config.get('credentials.new_password')
                    if not new_password:
                        print(f"{Fore.RED}❌ New password not configured. Please set 'credentials.new_password' in config.yaml{Style.RESET_ALL}")
                        await self.close_browser()
                        return False
                    action = self.pause_for_manual_work("Step 4: Password Change", 
                                                      f"About to change admin password to '{new_password}'")
                    if action == "quit":
                        await self.close_browser()
                        return False
                    elif action == "continue":
                        if not await self.change_password():
                            await self.close_browser()
                            if attempt < max_retries:
                                continue
                            return False
                    elif action == "skip":
                        print(f"{Fore.BLUE}⚠️ Skipping password change{Style.RESET_ALL}")
                
                # Step 5: Re-login with new password
                if start_from_step <= 5:
                    action = self.pause_for_manual_work("Step 5: Re-login", 
                                                      "About to re-login with new password")
                    if action == "quit":
                        await self.close_browser()
                        return False
                    elif action == "continue":
                        if not await self.relogin_with_new_password():
                            await self.close_browser()
                            if attempt < max_retries:
                                continue
                            return False
                    elif action == "skip":
                        print(f"{Fore.BLUE}⚠️ Assuming you're already logged in with new password{Style.RESET_ALL}")
                
                # Step 6: Configure network
                if start_from_step <= 6:
                    action = self.pause_for_manual_work("Step 6: Network Config", 
                                                      "About to configure network to use Cellular")
                    if action == "quit":
                        await self.close_browser()
                        return False
                    elif action == "continue":
                        if not await self.configure_network():
                            await self.close_browser()
                            if attempt < max_retries:
                                continue
                            return False
                    elif action == "skip":
                        print(f"{Fore.BLUE}⚠️ Skipping network configuration{Style.RESET_ALL}")
                
                # Step 7: Configure WiFi password
                if start_from_step <= 7:
                    wifi_encryption = self.config.get('wifi.encryption', 'WPA-PSK')
                    action = self.pause_for_manual_work("Step 7: WiFi Security", 
                                                      f"About to configure WiFi password and {wifi_encryption} encryption")
                    if action == "quit":
                        await self.close_browser()
                        return False
                    elif action == "continue":
                        if not await self.configure_wifi_password():
                            await self.close_browser()
                            if attempt < max_retries:
                                continue
                            return False
                    elif action == "skip":
                        print(f"{Fore.BLUE}⚠️ Skipping WiFi configuration{Style.RESET_ALL}")
                
                await self.close_browser()
                print(f"{Fore.GREEN}🎉 Successfully configured {ssid}!{Style.RESET_ALL}")
                return True
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️ Configuration interrupted by user{Style.RESET_ALL}")
                await self.close_browser()
                raise
                
            except Exception as e:
                print(f"{Fore.RED}❌ Configuration failed for {ssid} (attempt {attempt + 1}): {e}{Style.RESET_ALL}")
                await self.close_browser()
                
                if attempt < max_retries:
                    print(f"{Fore.BLUE}🔄 Will retry in 5 seconds...{Style.RESET_ALL}")
                    continue
                else:
                    print(f"{Fore.RED}❌ All retry attempts exhausted for {ssid}{Style.RESET_ALL}")
                    return False
        
        return False

def select_gateways(networks: List[Dict[str, str]]) -> List[str]:
    """CLI interface for selecting gateways to configure"""
    if not networks:
        print(f"{Fore.RED}❌ No Gateway networks found{Style.RESET_ALL}")
        return []
    
    print(f"\n{Fore.CYAN}📋 Found Gateway Networks:{Style.RESET_ALL}")
    none_count = 0
    secured_count = 0
    
    for i, network in enumerate(networks, 1):
        security_color = Fore.GREEN if network['security'] == 'None' else Fore.YELLOW
        print(f"{i:2d}. {network['ssid']} (Signal: {network['signal']}, Security: {security_color}{network['security']}{Style.RESET_ALL})")
        if network['security'] == 'None':
            none_count += 1
        else:
            secured_count += 1
    
    print(f"\n{Fore.CYAN}📊 Summary: {none_count} open networks, {secured_count} secured networks{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}Select gateways to configure:{Style.RESET_ALL}")
    print("• Enter numbers separated by commas (e.g., 1,3,5)")
    print("• Enter 'all' for all gateways")
    print(f"• Enter 'allnone' for all open gateways ({none_count} networks)")
    
    while True:
        try:
            selection = input("> ").strip().lower()
            
            if selection == 'all':
                return [network['ssid'] for network in networks]
            
            if selection == 'allnone':
                none_networks = [network['ssid'] for network in networks if network['security'] == 'None']
                if none_networks:
                    print(f"{Fore.GREEN}✅ Selected {len(none_networks)} open networks: {', '.join(none_networks)}{Style.RESET_ALL}")
                    return none_networks
                else:
                    print(f"{Fore.YELLOW}⚠️ No open networks found{Style.RESET_ALL}")
                    continue
            
            if not selection:
                continue
                
            indices = [int(x.strip()) for x in selection.split(',')]
            
            # Validate indices
            if all(1 <= i <= len(networks) for i in indices):
                selected_networks = [networks[i-1]['ssid'] for i in indices]
                return selected_networks
            else:
                print(f"{Fore.RED}❌ Invalid selection. Please enter numbers between 1 and {len(networks)}{Style.RESET_ALL}")
                
        except (ValueError, IndexError):
            print(f"{Fore.RED}❌ Invalid input. Please enter numbers separated by commas, 'all', or 'allnone'{Style.RESET_ALL}")

@click.command()
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--timeout', default=30, help='Timeout for each configuration step (seconds)')
@click.option('--interactive', '-i', is_flag=True, help='Enable interactive mode with pause/resume capability')
@click.option('--start-from', default=1, help='Start from specific step (1-7)', type=click.IntRange(1, 7))
def main(headless: bool, timeout: int, interactive: bool, start_from: int):
    """
    UG63 LoRaWAN Gateway Configuration Bot
    
    Automates the configuration of multiple UG63 gateways by scanning for
    Gateway_* WiFi networks and applying the standard configuration.
    """
    print(f"{Fore.CYAN}🤖 UG63 Gateway Configuration Bot{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}\n")
    
    async def run_bot():
        if interactive:
            print(f"{Fore.MAGENTA}🎮 Interactive Mode Enabled{Style.RESET_ALL}")
            print(f"{Fore.BLUE}You can pause at each step to do manual work{Style.RESET_ALL}")
        
        if start_from > 1:
            print(f"{Fore.BLUE}📍 Starting from step {start_from}{Style.RESET_ALL}")
        
        bot = GatewayConfigBot(interactive_mode=interactive)
        
        # Scan for Gateway networks
        networks = await bot.wifi_manager.scan_gateway_networks()
        
        if not networks:
            print(f"{Fore.RED}❌ No Gateway networks found. Please make sure gateways are powered on and broadcasting.{Style.RESET_ALL}")
            return
        
        # Let user select which gateways to configure
        selected_gateways = select_gateways(networks)
        
        if not selected_gateways:
            print(f"{Fore.YELLOW}⚠️ No gateways selected. Exiting.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.GREEN}✅ Selected {len(selected_gateways)} gateway(s) for configuration{Style.RESET_ALL}")
        
        # Configure each selected gateway
        success_count = 0
        for i, ssid in enumerate(selected_gateways, 1):
            print(f"\n{Fore.MAGENTA}📍 Processing gateway {i}/{len(selected_gateways)}: {ssid}{Style.RESET_ALL}")
            
            if await bot.configure_single_gateway(ssid, start_from_step=start_from):
                success_count += 1
            else:
                print(f"{Fore.RED}❌ Failed to configure {ssid}{Style.RESET_ALL}")
                
                # Ask if user wants to continue
                continue_choice = input(f"{Fore.YELLOW}Continue with remaining gateways? (y/n): {Style.RESET_ALL}").lower()
                if continue_choice not in ['y', 'yes']:
                    break
        
        # Summary
        print(f"\n{Fore.CYAN}📊 Configuration Summary:{Style.RESET_ALL}")
        print(f"✅ Successfully configured: {success_count}/{len(selected_gateways)} gateways")
        
        if success_count == len(selected_gateways):
            print(f"{Fore.GREEN}🎉 All gateways configured successfully!{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️ Some gateways failed. Please check the logs above.{Style.RESET_ALL}")
    
    # Run the bot
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
