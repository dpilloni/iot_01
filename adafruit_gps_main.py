import umqtt_robust2 as mqtt
from machine import UART
from time import sleep
from gps_bare_minimum import GPS_Minimum
from neopixel import NeoPixel
from machine import Pin

# CONFIGURATION
gps_port = 2                               # ESP32 UART port, Educaboard ESP32 default UART port
gps_speed = 9600                           # UART speed, defauls u-blox speed

# OBJECTS
uart = UART(gps_port, gps_speed)           # UART object creation
gps = GPS_Minimum(uart)                    # GPS object creation


pb1 = Pin(4, Pin.IN)
n = 12
p = 26
np = NeoPixel(Pin(p, Pin.OUT), n)


def set_neopixel(color):
    rgb = (0,0,0)
    
    if color == "red":
        rgb = (10, 0, 0)
    if color == "green":
        rgb = (0, 10, 0)
    for i in range(n):
        np[i] = rgb
    np.write()
    
      
set_neopixel("")

def get_adafruit_gps():
    if gps.receive_nmea_data():
        
        if gps.get_speed() != 0 and gps.get_latitude() != -999.0 and gps.get_longitude() != -999.0:
            
            speed =str(gps.get_speed())
            lat = str(gps.get_latitude())
            lon = str(gps.get_longitude())
            
            set_neopixel("green")
            return speed + "," + lat + "," + lon + "," + "0.0"
        else: 
            return False
    else:
        set_neopixel("red")
        print("waiting for GPS data - move GPS to place with access to the sky...")
        return False
        

while True:
    try:
        gps_data = get_adafruit_gps()
        if gps_data: 
            print(f'\ngps_data er: {gps_data}')
            mqtt.web_print(get_adafruit_gps(), 'CHFR0001/feeds/ESP32Feed/csv')
        sleep(4) 
        
        
        if len(mqtt.besked) != 0: 
            mqtt.besked = ""            
        mqtt.sync_with_adafruitIO()             
        print(".", end = '')
        
    
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        mqtt.c.disconnect()
        mqtt.sys.exit()