#!/bin/bash
# EC2 Ubuntu setup script

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Clone repository (replace with your repo URL)
git clone https://github.com/ABS-IISC/CT_TOOL.git
cd CT_TOOL

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p uploads outputs

# Install and configure nginx (optional)
sudo apt install nginx -y

# Create systemd service
sudo tee /etc/systemd/system/ct-review-tool.service > /dev/null <<EOF
[Unit]
Description=CT Review Tool
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/CT_TOOL
Environment=PATH=/home/ubuntu/CT_TOOL/venv/bin
ExecStart=/home/ubuntu/CT_TOOL/venv/bin/python run.py production
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ct-review-tool
sudo systemctl start ct-review-tool

echo "Setup complete! Service running on port 5000"