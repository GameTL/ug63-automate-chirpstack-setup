#!/bin/bash
# Quick setup script for UG63 Gateway Config Bot using uv

set -e

echo "🤖 UG63 Gateway Config Bot - Quick Setup with uv"
echo "================================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "📦 Installing dependencies with uv..." 
uv sync

echo "🌐 Installing Playwright browsers..."
uv run playwright install chromium

# Check if config.yaml exists and has placeholder values
CONFIG_EXISTS=false
HAS_PLACEHOLDERS=false

if [ -f "config.yaml" ]; then
    CONFIG_EXISTS=true
    # Check if config.yaml contains placeholder values
    if grep -q "\${NEW_GATEWAY_ADMIN_PASSWORD}\|\${NEW_GATEWAY_WIFI_PASSWORD}" config.yaml; then
        HAS_PLACEHOLDERS=true
    fi
fi

# Create or update config.yaml if it doesn't exist or has placeholders
if [ "$CONFIG_EXISTS" = false ] || [ "$HAS_PLACEHOLDERS" = true ]; then
    if [ "$CONFIG_EXISTS" = true ]; then
        echo "📝 Updating config.yaml file (found placeholder values)..."
    else
        echo "📝 Creating config.yaml file..."
    fi
    
    # Prompt for credentials and ChirpStack settings
    echo ""
    echo "🔐 Please provide the following credentials:"
    echo ""
    
    read -p "Enter new admin username (default: admin): " NEW_USERNAME
    NEW_USERNAME=${NEW_USERNAME:-admin}
    
    read -s -p "Enter new admin password: " NEW_ADMIN_PASSWORD
    echo ""
    
    read -s -p "Enter new WiFi password: " NEW_WIFI_PASSWORD
    echo ""
    
    echo ""
    echo "📡 Please provide ChirpStack server settings:"
    echo ""
    
    read -p "Enter ChirpStack server address (default: 192.168.1.1): " CHIRPSTACK_SERVER
    CHIRPSTACK_SERVER=${CHIRPSTACK_SERVER:-192.168.1.1}
    
    read -p "Enter ChirpStack server port (default: 1883): " CHIRPSTACK_PORT
    CHIRPSTACK_PORT=${CHIRPSTACK_PORT:-1883}
    
    # Create config.yaml with placeholders first
    cat > config.yaml << 'EOF'
# UG63 Gateway Configuration Settings

# ChirpStack Configuration
chirpstack: 
  server_address: "192.168.1.1"
  server_port: 1883
  protocol: "ChirpStack-v4"

# Gateway Credentials
credentials:
  default_username: "admin"
  default_password: "password"
  new_username: "admin"
  new_password: "${NEW_GATEWAY_ADMIN_PASSWORD}"

# WiFi Configuration
wifi:
  password: "${NEW_GATEWAY_WIFI_PASSWORD}"
  encryption: "WPA-PSK"
  scan_pattern: "Gateway_"

# Network Configuration
network:
  connection_type: "Cellular"  # Options: WAN, Cellular
  
# Browser Configuration
browser:
  headless: false
  timeout: 30000  # milliseconds
  slow_mo: 0      # milliseconds between actions
  
# Gateway Web Interface
web_interface:
  ip_address: "192.168.1.1"
  protocol: "http"
  
# Timeouts (seconds)
timeouts:
  wifi_connection: 10
  page_load: 30
  form_submit: 10
  password_change: 15
EOF
    
    # Replace placeholders with actual values (fix the variable names)
    sed -i.bak "s/\${NEW_GATEWAY_ADMIN_PASSWORD}/${NEW_ADMIN_PASSWORD}/g" config.yaml
    sed -i.bak "s/\${NEW_GATEWAY_WIFI_PASSWORD}/${NEW_WIFI_PASSWORD}/g" config.yaml
    sed -i.bak "s/new_username: \"admin\"/new_username: \"${NEW_USERNAME}\"/g" config.yaml
    sed -i.bak "s/server_address: \"192.168.1.1\"/server_address: \"${CHIRPSTACK_SERVER}\"/g" config.yaml
    sed -i.bak "s/server_port: 1883/server_port: ${CHIRPSTACK_PORT}/g" config.yaml
    
    # Clean up backup file
    rm config.yaml.bak
    
    echo "✅ config.yaml created/updated with your credentials"
    echo "🔐 Admin username: ${NEW_USERNAME}"
    echo "🔐 Admin password: [HIDDEN]"
    echo "🔐 WiFi password: [HIDDEN]"
    echo "📡 ChirpStack server: ${CHIRPSTACK_SERVER}:${CHIRPSTACK_PORT}"
else
    echo "📄 config.yaml already exists and appears to be configured, skipping creation"
    echo "💡 To update credentials, edit config.yaml manually or delete it and run this script again"
fi

echo "🧪 Running setup tests..."
uv run python test_setup.py

echo ""
echo "✅ Setup complete! You can now run the bot with:"
echo "   uv run python gateway_config_bot.py"
echo ""
echo "💡 Other useful commands:"
echo "   uv run ug63-config      # Run the bot using the script entry point"
echo "   uv run ug63-test        # Test your setup"
echo "   uv run --help           # Show uv help"
echo ""
echo "📚 For more information, check the README.md file"
