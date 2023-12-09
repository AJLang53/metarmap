METARMAP
========
Software for running a custom METAR MAP, which retrieves and maintains METAR data, and uses it to
drive LEDs for given stations

Only implementated and tested with Raspberry Pi Zero W using WS2811 addressable LEDs, retrieving
data from the aviationweather.gov data api

Create your own LED_Driver and/or METAR_SOURCE implementing the protocols to work with something different

See samples for run examples

Auto-Run on Raspberry Pi
------------------------
I struggled to get this running on bootup on the Raspberry Pi using cron given the use of virtual environments, and the neopixel library requiring root access.

I was eventually successful by creating a bash script (see data/run_map.sh) and running the module as a service with SYSTEMD Unit file (see data/metarmap.service). These .service files can be placed in /etc/systemd/system, and you can
check on the status of a service by running:
    sudo systemctl status "service_name"