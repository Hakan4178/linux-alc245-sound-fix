#!/bin/bash
# install.sh - linux-alc245-sound-fix
# Tested on Kali / Debian-based systems

set -e

echo "🔧 Installing linux-alc245-sound-fix"
echo "=============================================="


# 2. Required system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    libportaudio2 \
    portaudio19-dev \
    libasound2-dev \
    alsa-utils \
    git \
    python3-evdev

# 3. Clone or update repository
echo "📥 Fetching project repository..."
if [ -d "linux-alc245-sound-fix" ]; then
    echo "⚠️  Repository already exists, updating..."
    cd linux-alc245-sound-fix
    git pull
else
    git clone https://github.com/Hakan4178/linux-alc245-sound-fix.git
    cd linux-alc245-sound-fix
fi

# 4. Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# 5. Install Python dependencies inside venv
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install numpy sounddevice evdev
deactivate

echo ""
echo "🎉 Installation completed successfully!"
echo "======================================="
echo ""
echo "▶ How to run:"
echo "cd linux-alc245-sound-fix && sudo -E venv/bin/python quick_hardening.py"
echo "⚠️  NOTE:"
echo "- sudo is required for input/audio device access"
echo "- Do NOT use system python or pip outside the virtual environment"
echo ""
echo "💡 Tip:"
echo "You can install this as a systemd service for automatic startup."
