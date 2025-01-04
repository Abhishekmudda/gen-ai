# setup.sh
#sudo chmod +x /home/user/.wdm/drivers/chromedriver/linux64/*/chromedriver
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list'
sudo apt update
sudo apt install microsoft-edge-stable
EDGE_VERSION=$(microsoft-edge --version | awk '{print $3}')
curl -O https://msedgedriver.azureedge.net/$EDGE_VERSION/edgedriver_linux64.zip
unzip edgedriver_linux64.zip -d /usr/local/bin/

# sudo apt update
# sudo apt install firefox
# GECKODRIVER_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep "tag_name" | awk -F '"' '{print $4}')
# curl -LO "https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz"
# tar -xvzf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz
# sudo mv geckodriver /usr/local/bin/



