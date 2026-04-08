#!/bin/bash

# SHx Tip Bot - Systemd Service Setup Script
# Run this script on your Raspberry Pi to make the bot run 24/7 and survive reboots.

BOT_DIR=$(pwd)
USER_NAME=$(whoami)

# Detect if a virtual environment is being used
if [ -f "$BOT_DIR/venv/bin/python" ]; then
    PYTHON_EXEC="$BOT_DIR/venv/bin/python"
elif [ -f "$BOT_DIR/venv/bin/python3" ]; then
    PYTHON_EXEC="$BOT_DIR/venv/bin/python3"
else
    PYTHON_EXEC="/usr/bin/python3"
fi

echo "Setting up SHx Tip Bot Service..."
echo "Bot Directory: $BOT_DIR"
echo "Python Executable: $PYTHON_EXEC"
echo "User: $USER_NAME"

SERVICE_FILE="/etc/systemd/system/shxbot.service"

cat <<EOF | sudo tee $SERVICE_FILE > /dev/null
[Unit]
Description=SHx Tip Bot Discord Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$BOT_DIR
ExecStart=$PYTHON_EXEC $BOT_DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable shxbot.service
sudo systemctl restart shxbot.service

echo "=========================================================="
echo "✅ Setup Complete!"
echo "The bot is now running in the background."
echo "It will automatically start whenever the Raspberry Pi reboots."
echo ""
echo "Helpful Commands:"
echo "  Check Status : sudo systemctl status shxbot"
echo "  View Logs    : sudo journalctl -u shxbot -n 50 -f"
echo "  Stop Bot     : sudo systemctl stop shxbot"
echo "  Start Bot    : sudo systemctl start shxbot"
echo "  Restart Bot  : sudo systemctl restart shxbot"
echo "=========================================================="
