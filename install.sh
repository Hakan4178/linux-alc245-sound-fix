#!/bin/bash
# install.sh - linux-alc245-sound-fix

set -e

echo "🔧 linux-alc245-sound-fix kuruluyor..."
echo "=============================================="

# 1. Sistem güncellemeleri
echo "📦 Sistem güncelleniyor..."
sudo apt update
sudo apt upgrade -y

# 2. Gerekli sistem paketleri
echo "📦 Bağımlılıklar yükleniyor..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    libportaudio2 \
    libasound2-dev \
    alsa-utils \
    portaudio19-dev \
    python3-dev \
    git \
    python3-evdev  # evdev için sistem paketi ekle

# 3. Projeyi indir
echo "📥 Proje indiriliyor..."
if [ -d "linux-alc245-sound-fix" ]; then
    echo "⚠️  Proje zaten var, güncelleniyor..."
    cd linux-alc245-sound-fix
    git pull
else
    git clone https://github.com/Hakan4178/linux-alc245-sound-fix.git
    cd linux-alc245-sound-fix
fi

# 4. Sanal ortam oluştur ve aktif et
echo "🐍 Python sanal ortamı oluşturuluyor..."
python3 -m venv venv
source venv/bin/activate

# 5. Python paketlerini kur
echo "📦 Python bağımlılıkları yükleniyor..."
pip install --upgrade pip
pip install numpy sounddevice

# evdev zaten sistemde yüklü, fakat Python binding'ini de yükle
pip install evdev

echo ""
echo "🎉 Kurulum tamamlandı!"
echo "======================="
echo ""
echo "🔧 Çalıştırmak için:"
echo "1. cd linux-alc245-sound-fix"
echo "2. source venv/bin/activate"
echo "3. sudo python3 quick_hardening.py"
echo ""
echo "⚠️  NOT: Script'i çalıştırmak için sudo gereklidir (evdev cihaz erişimi için)"
