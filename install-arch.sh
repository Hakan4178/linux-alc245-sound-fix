#!/bin/bash
# install-arch.sh - linux-alc245-sound-fix
# Tested on Arch Linux / Arch-based systems

set -e

echo "🔧 Installing linux-alc245-sound-fix (Arch Linux)"
echo "================================================"

# 1. System update (optional but recommended)
echo "📦 Updating system..."
sudo pacman -Syu --noconfirm

# 2. Install required system dependencies
echo "📦 Installing system dependencies..."
sudo pacman -S --needed --noconfirm \
    python \
    python-pip \
    python-virtualenv \
    portaudio \
    alsa-utils \
    git \
    playerctl \
    python-evdev

# PipeWire users may need JACK compatibility
if pacman -Qs pipewire-jack >/dev/null; then
    echo "🎧 pipewire-jack already installed"
else
    echo "🎧 Installing pipewire-jack for audio compatibility..."
    sudo pacman -S --needed --noconfirm pipewire-jack
fi

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
python -m venv venv

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
echo ""
echo "⚠️  NOTES:"
echo "- sudo is required for /dev/input and audio access"
echo "- Do NOT use system-wide pip"
echo "- Works with ALSA / PipeWire / JACK"
echo ""
echo "💡 Tip:"
echo "You can create a systemd service for automatic startup."
