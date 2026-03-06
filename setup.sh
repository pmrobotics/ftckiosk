#!/bin/bash

if grep -q "Raspberry Pi" /proc/device-tree/model
then 
  echo "* Setting up for Raspberry Pi environment"
  scripts/setup-raspi.sh
fi

if grep -q "ROCK3 Model C" proc/device-tree/model
then 
  echo "* Setting up for Raspberry Pi environment"
  scripts/setup-rock3c.sh
fi

PKGS="python3-jinja2 wlrctl xdotool cec-utils"
echo "* Install wlrctl/xdotool (enables mouse click for audio)..."
echo "  sudo apt --ignore-missing satisfy $PKGS"
sudo apt --ignore-missing satisfy $PKGS

echo "* Set up autostart file..."
TMP="/var/tmp/ftckiosk.desktop"
AUTOSTART_DIR="$HOME/.config/autostart"
cat <<END_AUTOSTART >$TMP
[Desktop Entry]
Type=Application
Name=FTCkiosk
Exec=sh -c "cd $PWD; systemd-inhibit --what=idle /usr/bin/python3 ftckiosk.py >>server.log 2>&1 &"
Terminal=true
END_AUTOSTART
echo "  Contents of $TMP:"
sed 's/^/    /' $TMP
echo "  mkdir -p $AUTOSTART_DIR"
mkdir -p $AUTOSTART_DIR
echo "  cp -i $TMP $AUTOSTART_DIR"
cp -i $TMP $AUTOSTART_DIR
