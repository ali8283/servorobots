#!/bin/bash
	while true;
	do
     	echo -------------------------------------------------------------
        declare -i err
    	err=0
    	echo Installing python libraries
    	sudo apt-get install python3 python3-flask python3-smbus
    	err=err+$?
        cd
        echo Installing the library to communicate with the arduino
        git clone https://github.com/pololu/pololu-rpi-slave-arduino-library
    	err=err+$?
    	echo Installing virtualenv
    	sudo pip3 install -U virtualenv
    	err=err+$?
    	if [ $err -gt 0 ];
        	then
        	echo Error during installation of python, pip3 or pololu library
        	break
    	fi
        echo -------------------------------------------------------------
        
        echo For VNC server
        sudo apt-get update
        err=err+$?
        sudo apt-get install realvnc-vnc-server
        err=err+$?
        echo Installing tensorflow
        sudo apt-get -y install libatlas-base-dev
        pip3 install --no-cache-dir --upgrade tensorflow
        err=err+$?
        cd
    	if [ $err -gt 0 ];
        	then
        	echo Tensorflow install failed
        	break
    	fi
    	echo -------------------------------------------------------------
        echo All dependencies installed
        echo -------------------------------------------------------------
        echo Enable VNC with
        echo sudo raspi-config
        echo Interface > VNC
        echo Install VNC viewer https://www.realvnc.com/en/connect/download/viewer/linux/ 
        echo follow the password instruction section here: https://www.raspberrypi.org/documentation/remote-access/vnc/
        # To install Arduino IDE
        # cd Downloads/
        #tar -xf arduino-1.8.3-linuxarm.tar.xz
        # sudo mv arduino-1.8.8 /opt
        # sudo /opt/arduino-1.8.8/install.sh
        # TODO automate this part in script, see: https://arduino.stackexchange.com/questions/14771/arduino-command-line-interface-how-to-change-boardsmanager-additional-urls/14773
        # Within VNC and the Adruino IDE, manually add a new board with https://files.pololu.com/arduino/package_pololu_index.json
        # Set the new board and Port (USB should auto detect the board)
        # Upload a test sketch such as Blink.ino and save it.
        # Test the upload with command line in C9
        # /opt/arduino-1.8.8/arduino --upload ~/Arduino/Blink/Blink.ino
        # Add  the RPi slave library
        # cd /home/pi/Arduino/libraries
        # git clone https://github.com/pololu/pololu-rpi-slave-arduino-library
        # mv pololu-rpi-slave-arduino-library PololuRPiSlave
        # Add the A-star 32U4 library
        # cd /home/pi/Arduino/libraries
        # git clone https://github.com/pololu/balboa-32u4-arduino-library
        # mv balboa-32u4-arduino-library Balboa32U4
        
	break
	done
