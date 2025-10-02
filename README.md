# UG63 LoRaWAN Gateway Configuration Bot 🤖

An automated browser bot for configuring multiple UG63 LoRaWAN gateways with standardized ChirpStack settings.

## Works with 
- v64.0.0.3
- v64.0.0.4

## Features ✨

- 🔍 Automatically scans for Gateway_* WiFi networks
- 📋 Interactive CLI for selecting gateways to configure
- 🔄 Loops through selected gateways for batch processing
- 🌐 Browser automation for web-based configuration
- 🔐 Changes default credentials for security
- 📡 Configures ChirpStack v4 integration
- 📶 Sets up cellular connectivity and WiFi security

## What the Bot Does 🚀

For each selected gateway, the bot will:

### Initial Login & ChirpStack Configuration
1. Connect to the Gateway_* WiFi network
2. Open browser and navigate to 192.168.1.1
3. Login with default credentials (admin/password)
4. Navigate to Packet Forward settings
5. Change from "Embedded NS" to "ChirpStack-v4"
6. Configure server address: `{url}:{port}`
7. Save and apply settings

### Security Configuration
1. Navigate to System → User settings
2. Change admin password from "password" to ${NEW_GATEWAY_ADMIN_PASSWORD}
3. Re-login with new credentials

### Network Configuration
1. Navigate to Network settings
2. Change connection type from "WAN" to "Cellular"
3. Navigate to WLAN settings
4. Change WiFi encryption from "No Encryption" to "WPA-PSK"
5. Set WiFi password to ${NEW_GATEWAY_WIFI_PASSWORD}
6. Save all settings

## Prerequisites 📋

- Python 3.8 or higher
- Internet connection for initial setup
- Administrator/sudo privileges for WiFi operations
- Chrome/Chromium browser (auto-installed by Playwright)

### Platform-Specific Requirements

**macOS:**
- Xcode command line tools: `xcode-select --install`
- May need to run with `sudo` for WiFi operations

**Linux: [Not Tested]**
- NetworkManager installed and running
- User added to netdev group or sudo privileges

**Windows: [Not Tested]**
- Run as administrator for WiFi operations

## Installation 🛠️

### Option 1: Using uv (Recommended)

#### Quick Setup
```bash
git clone <your-repo-url>
cd ug63-automate-chirpstack-setup
./uv-quickstart.sh
```

#### Manual Setup
1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or on Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Clone or download this repository:
   ```bash
   git clone <your-repo-url>
   cd ug63-automate-chirpstack-setup
   ```

3. Install dependencies and set up the project:
   ```bash
   uv sync
   uv run playwright install chromium
   ```

4. Test the setup (optional):
   ```bash
   uv run ug63-test
   ```

5. Run the bot:
   ```bash
   uv run python gateway_config_bot.py
   ```

### Option 2: Traditional pip installation

1. Clone or download this repository:
   ```bash
   git clone <your-repo-url>
   cd ug63-automate-chirpstack-setup
   ```

2. Run the setup script:
   ```bash
   python setup.py
   ```

   This will:
   - Install Python dependencies (tries uv first, falls back to pip)
   - Download Playwright browsers
   - Display platform-specific setup instructions

## Usage 🎯

### Basic Usage
> Note for MacOS: need to be connected to the first Gateway otherwise if WiFi is not connected to any device the system call for availiable WiFi will not work. 

Run the bot with default settings:
```bash
# With uv
uv run python gateway_config_bot.py

# Or if installed traditionally
python gateway_config_bot.py

# Or using the installed script (after uv sync)
uv run ug63-config
```

### Command Line Options

```bash
# Show help
uv run python gateway_config_bot.py --help

# Run with custom timeout (default: 30 seconds)
uv run python gateway_config_bot.py --timeout 45

# Run in headless mode (no visible browser window)
uv run python gateway_config_bot.py --headless

# Run in interactive mode (pause at each step)
uv run python gateway_config_bot.py --interactive

# Start from a specific step (useful after manual intervention)
uv run python gateway_config_bot.py --start-from 3

# Combine options
uv run python gateway_config_bot.py --interactive --start-from 2

# Test your setup
uv run ug63-test
```

### Interactive Flow

1. **WiFi Scanning**: The bot scans for networks starting with "Gateway_"
2. **Gateway Selection**: Choose which gateways to configure:
   - Enter numbers: `1,3,5` (configure gateways 1, 3, and 5)
   - Enter `all` (configure all found gateways)
   - Enter `allnone` (configure all open/unsecured gateways)
3. **Automated Configuration**: The bot processes each gateway sequentially
4. **Interactive Mode** (optional): Pause at each step for manual intervention
5. **Progress Updates**: Real-time status updates with color-coded output
6. **Error Handling**: Option to continue with remaining gateways if one fails

### Interactive Mode Features

When using `--interactive` mode, you can:

- **Pause & Resume**: Stop at any step to do manual configuration
- **Skip Steps**: Skip steps you've already completed manually  
- **Start from Specific Step**: Resume from where you left off using `--start-from N`
- **Manual Override**: Handle tricky cases manually while automating the rest

**Configuration Steps:**
1. WiFi Connection
2. Browser & Login  
3. ChirpStack Configuration
4. Password Change
5. Re-login
6. Network Configuration  
7. WiFi Security Setup

Example workflow:
```bash
# Start interactive mode
uv run python gateway_config_bot.py --interactive

# Hit a problem at step 4? Quit and resume from step 4
uv run python gateway_config_bot.py --interactive --start-from 4

# Skip the tricky step and continue
# (at the pause prompt, choose 's' for skip)
```

## Configuration Details ⚙️

### Default Settings Applied

| Setting | Value |
|---------|--------|
| ChirpStack Server | `${SERVER_IP_ADDRESS}` |
| ChirpStack Port | `${SERVER_PORT}` |
| Admin Password | `${NEW_GATEWAY_ADMIN_PASSWORD}` |
| WiFi Password | `${NEW_GATEWAY_WIFI_PASSWORD}}$` |
| Network Type | Cellular |
| WiFi Encryption | WPA-PSK |

### Customization

To modify default values, edit the following in `gateway_config_bot.py`:

```python
# ChirpStack settings
await self.page.fill('#cs4_address', 'your-server.com')
await self.page.fill('input[name="cs4_port"]', 'your-port')

# Password settings
new_password = "your_password"
wifi_password = "your_wifi_password"
```

## Troubleshooting 🔧

### Common Issues

**WiFi Connection Fails:**
- Ensure gateways are powered on and broadcasting
- Check if your system requires sudo/admin privileges
- Verify network adapter is enabled

**Browser Automation Fails:**
- Gateway web interface may be slow - increase timeout
- Check if 192.168.1.1 is accessible after WiFi connection
- Ensure no firewall blocking the connection

**Permission Errors:**
- Run with `sudo` on macOS/Linux or as administrator on Windows
- Add user to appropriate groups (netdev on Linux)

### Debug Mode

For detailed debugging, modify the browser launch in `gateway_config_bot.py`:
```python
self.browser = await playwright.chromium.launch(
    headless=False,  # Show browser
    slow_mo=1000,    # Slow down actions
    devtools=True    # Show dev tools
)
```

## Dependencies 📦

### Production Dependencies
- **playwright**: Browser automation
- **click**: CLI interface
- **colorama**: Cross-platform colored output
- **psutil**: System utilities
- **pyyaml**: Configuration file support

### Development Dependencies (optional)
Install with: `uv sync --extra dev`
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing framework

### uv Commands

```bash
# Install all dependencies (including dev)
uv sync --extra dev

# Run with development dependencies
uv run --extra dev python gateway_config_bot.py

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy gateway_config_bot.py

# Run tests
uv run pytest
```

## Security Notes 🔒

- The bot changes default credentials for security
- Passwords are hardcoded - modify for production use
- Consider using environment variables for sensitive data
- The bot requires elevated privileges for WiFi operations

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with actual UG63 hardware
5. Submit a pull request

## License 📄

This project is provided as-is for automation purposes. Use responsibly and in accordance with your organization's policies.

## Support 💬

For issues or questions:
1. Check the troubleshooting section
2. Review the gateway's web interface manually
3. Test WiFi connectivity separately
4. Open an issue with detailed logs

---

**Happy Gateway Configuring! 🚀📡**
