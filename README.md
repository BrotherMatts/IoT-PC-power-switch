# IoT-PC-power-switch 

This is a testing implementation of replacing PC power switch with an IoT-board. This will be improved to a *more production ready implementation* as time goes on.

Code is written in MicroPython and is currently deployed and working as expected on a Raspberry Pi Pico W board. During testing phase I also ran this code on an ESP32S2 board succesfully.

End goal of this implementation is to allow controlling PC power by voice, which is achieved by connecting this piece of code to an MQTT broker and relaying Google Assistant (in this case through a Raspberry Pi 4 Home Assistant server) to the IoT board. This is currently working as expected in my case.
