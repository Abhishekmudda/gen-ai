#!/bin/bash

# setup.sh
set -e  # Exit on any error

echo "Starting Microsoft Edge and EdgeDriver setup..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y curl unzip gpg apt-transport-https ca-certificates

# Setup Microsoft Edge repository
echo "Setting up Microsoft Edge repository..."
curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /tmp/microsoft.gpg
install -o root -g root -m 644 /tmp/microsoft.gpg /etc/apt/trusted.gpg.d/
sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list'
rm /tmp/microsoft.gpg

# Install Edge
echo "Installing Microsoft Edge..."
apt-get update
apt-get install -y microsoft-edge-stable

# Get Edge version and install matching driver
echo "Installing EdgeDriver..."
EDGE_VERSION=$(microsoft-edge --version | awk '{print $3}')
echo "Detected Edge version: $EDGE_VERSION"

DRIVER_DIR="/usr/local/bin"
TEMP_DIR=$(mktemp -d)

# Download and install EdgeDriver
cd "$TEMP_DIR"
curl -Lo edgedriver_linux64.zip "https://msedgedriver.azureedge.net/$EDGE_VERSION/edgedriver_linux64.zip"
unzip edgedriver_linux64.zip
chmod +x msedgedriver
mv msedgedriver "$DRIVER_DIR/"

# Cleanup
cd - > /dev/null
rm -rf "$TEMP_DIR"

echo "Setup complete. EdgeDriver installed at: $DRIVER_DIR/msedgedriver"
echo "Edge version: $EDGE_VERSION"

# Verify installation
if command_exists microsoft-edge && [ -x "$DRIVER_DIR/msedgedriver" ]; then
    echo "Installation verified successfully"
    exit 0
else
    echo "Installation verification failed"
    exit 1
fi





