# ftckiosk - FTC kiosk / display manager for SBC

This is a (childishly) simple display manager server to help remotely set up FIRST Tech Challenge field timers on Raspberry Pi (RPi) devices.

The Raspberry Pi 5 and Raspberry Pi 4 devices work great to drive field timer displays, but they often require visiting each device with a keyboard and/or mouse to connect them to the FTC Live scoring system on a local network.  Or, they need to be configured to run with desktop sharing via VNC and driven from a VNC client.

This software provides a simple HTTP server that can be installed on the RPi and run at startup/boot.  It advertises the RPI's network addresses on the RPi display, browsers on the scoring computer/network can then connect to the RPi to start a display for a given event.

## Installation

Installation is simple:  

1. Open a terminal window
2. Unpack the software into an accessible directory (we use $HOME/ftckiosk)
3. Change to the software directory
4. Run the setup.sh script

The setup.sh script will prompt for super-user access as needed (via sudo).

The setup script does four basic tasks:
1. Via raspi-config it turns off screen blanking, enables SSH and VNC
2. Via systemctl it disables the cups-browsed (printer) and bluetooth services
3. Installs the wlrctl and xdotool packages to enable a remote mouse click
4. Creates a $HOME/.config/autoexec/ftckiosk.desktop file to automatically start the ftckiosk.py server upon login.


