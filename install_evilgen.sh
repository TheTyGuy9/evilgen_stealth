#!/bin/bash
# Universal Phishlet Generator Installer

echo "=== Universal Phishlet Generator Installation ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[!] Python3 not found. Installing..."
    sudo apt update
    sudo apt install python3 python3-pip -y
fi

# Install Python dependencies
echo "[*] Installing Python dependencies..."
pip3 install selenium browsermob-proxy pyyaml colorama requests

# Install Chrome and Chromedriver
echo "[*] Installing Chrome and Chromedriver..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable -y

# Install latest chromedriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip

# Download BrowserMob Proxy
echo "[*] Setting up BrowserMob Proxy..."
wget -q https://github.com/lightbody/browsermob-proxy/releases/download/browsermob-proxy-2.1.4/browsermob-proxy-2.1.4-bin.zip
unzip -q browsermob-proxy-2.1.4-bin.zip
chmod +x browsermob-proxy-2.1.4/bin/browsermob-proxy

# Make main script executable
chmod +x phishletgen_universal.py

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "Usage:"
echo "  python3 phishletgen_universal.py"
echo ""
echo "Features:"
echo "  - Supports Evilginx 1, 2, and 3"
echo "  - Interactive wizard"
echo "  - Automatic form detection"
echo "  - Traffic analysis"
echo "  - Cookie/session detection"
echo ""
echo "Legal reminder: Use only in authorized lab environments!"