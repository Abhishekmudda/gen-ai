# setup.sh
#sudo chmod +x /home/user/.wdm/drivers/chromedriver/linux64/*/chromedriver
# Step 1: Add Microsoft GPG key for package verification
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg

# Step 2: Move the GPG key to trusted apt sources
sudo install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/

# Step 3: Add Microsoft Edge repository to apt sources
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list'

# Step 4: Update apt package lists
sudo apt update

# Step 5: Install Microsoft Edge
sudo apt install microsoft-edge-stable

# Step 6: Get the installed version of Microsoft Edge
EDGE_VERSION=$(microsoft-edge --version | awk '{print $3}')

# Step 7: Download the corresponding version of EdgeDriver
curl -O https://msedgedriver.azureedge.net/$EDGE_VERSION/edgedriver_linux64.zip

# Step 8: Unzip and install EdgeDriver
unzip edgedriver_linux64.zip -d /usr/local/bin/


# sudo apt update
# sudo apt install firefox
# GECKODRIVER_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep "tag_name" | awk -F '"' '{print $4}')
# curl -LO "https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz"
# tar -xvzf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz
# sudo mv geckodriver /usr/local/bin/



