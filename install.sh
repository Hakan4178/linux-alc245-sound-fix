#!/bin/bash
# install.sh - linux-alc245-sound-fix

set -e  

echo "🔧 linux-alc245-sound-fix ..."
echo "=============================================="

# 1. Sistem güncellemeleri
echo "📦 System upgradeing..."
sudo apt update
sudo apt upgrade -y

# 2. Gerekli sistem paketleri
echo "📦 İnstall dependies..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    libportaudio2 \
    libasound2-dev \
    alsa-utils \
    portaudio19-dev \
    python3-dev \
    git

# 3. Projeyi indir
echo "📥 Project download..."
if [ -d "linux-alc245-sound-fix" ]; then
    echo "⚠️  , ???? ..."
    cd linux-alc245-sound-fix
    git pull
else
    git clone https://github.com/Hakan4178/linux-alc245-sound-fix.git
    cd linux-alc245-sound-fix
fi

# 4. Sanal ortam oluştur
echo "🐍 Python ..."
python3 -m venv venv

# 5. Sanal ortamı etkinleştir
echo "🔧 Very important ..."
source venv/bin/activate

# 6. Python paketlerini kur
echo "📦 Python dependies ..."
pip install --upgrade pip
pip install numpy sounddevice evdev

echo ""
echo "🎉 Finished!"
echo "======================="
