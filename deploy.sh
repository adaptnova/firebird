#!/bin/bash

# Usage: ./deploy.sh <user>@<ip>

TARGET=$1

if [ -z "$TARGET" ]; then
    echo "Usage: ./deploy.sh <user>@<ip>"
    exit 1
fi

echo "🚀 Deploying Firebird to $TARGET..."

# 1. Sync Files
echo "📦 Syncing files..."
rsync -avz --exclude '.git' --exclude '__pycache__' \
    /adapt/projects/firebird/ \
    $TARGET:~/firebird/

# 2. Setup Remote Environment
echo "🔧 Setting up remote environment..."
ssh $TARGET << 'EOF'
    # Install System Dependencies
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv curl

    # Install Temporal CLI
    if ! command -v temporal &> /dev/null; then
        echo "Installing Temporal..."
        curl -sSf https://temporal.download/cli.sh | sh
        echo 'export PATH="$PATH:$HOME/.temporalio/bin"' >> ~/.bashrc
    fi

    # Setup Python Environment
    cd ~/firebird/agents/immortal
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Setup Systemd Services
    mkdir -p ~/.config/systemd/user
    
    # Temporal Service
    cat > ~/.config/systemd/user/temporal.service << 'SERVICE'
[Unit]
Description=Temporal Server
After=network.target

[Service]
ExecStart=%h/.temporalio/bin/temporal server start-dev --ip 0.0.0.0 --ui-port 8233
Restart=always

[Install]
WantedBy=default.target
SERVICE

    # Agent Service
    cat > ~/.config/systemd/user/immortal-agent.service << 'SERVICE'
[Unit]
Description=Immortal Agent
After=network.target temporal.service

[Service]
ExecStart=%h/firebird/agents/immortal/venv/bin/python3 %h/firebird/agents/immortal/temporal_agent.py
WorkingDirectory=%h/firebird/agents/immortal
Restart=always
Environment=SESSION_ID=production_v1
# Add other env vars here or load from file

[Install]
WantedBy=default.target
SERVICE

    # Reload and Start
    systemctl --user daemon-reload
    systemctl --user enable --now temporal
    systemctl --user enable --now immortal-agent
    
    # Enable lingering so services stay up after logout
    loginctl enable-linger $USER
EOF

echo "✅ Deployment Complete! Agent should be running."
echo "Check status with: ssh $TARGET 'systemctl --user status immortal-agent'"
