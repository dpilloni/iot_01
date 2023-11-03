#############################################
# MQTT og wifi modul fra undervisning d.: 11/09/2023
# tilrettet af Daniel F. Pilloni
############################################

from robust2 import MQTTClient #MQTT client script
import sys
import network
import os
from credentials import credentials

#WIFI 
def connect_2_wifi():    
    wifi.active(True)
    try:
        wifi.connect(WIFI_SSID, WIFI_PASSWORD) #forbind til internettet
        wifi.config(txpower=4)  # In dBm
    except:
        return False

def status_wifi():
    return wifi.isconnected()

def status_ada():
    return c.is_conn_issue()

#MQTT
def sent_MQTT(text_in, feed):
    mqtt_preb_feedname = '{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, feed)
    c.publish(topic=bytes(mqtt_preb_feedname, 'utf-8'), msg=str(text_in))
    
def sub_cb(topic, msg, retained, duplicate):
    return False
    #print((topic, msg, retained, duplicate))

def sync_with_adafruitIO(): 
    # haandtere fejl i forbindelsen og hvor ofte den skal forbinde igen
    if c.is_conn_issue():
        while c.is_conn_issue():
            # hvis der forbindes returnere is_conn_issue metoden ingen fejlmeddelse
            c.reconnect()
        else:
            c.resubscribe()
    c.check_msg() # needed when publish(qos=1), ping(), subscribe()
    c.send_queue()  # needed when using the caching capabilities for unsent messages
   
WIFI_SSID = credentials["ssid"] 
WIFI_PASSWORD = credentials["password"]

# turn off the WiFi Access Point
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
wifi = network.WLAN(network.STA_IF)

if (wifi.isconnected()):
    wifi.disconnect()#Fixer WiFi OS fejl!

# connect to Adafruit IO MQTT broker using unsecure TCP (port 1883)
#
# To use a secure connection (encrypted) with TLS:
#   set MQTTClient initializer parameter to "ssl=True"
#   Caveat: a secure connection uses about 9k bytes of the heap
#         (about 1/4 of the micropython heap on the ESP8266 platform)
ADAFRUIT_IO_URL = credentials["ADAFRUIT_IO_URL"]
ADAFRUIT_USERNAME = credentials["ADAFRUIT_USERNAME"]
ADAFRUIT_IO_KEY = credentials["ADAFRUIT_IO_KEY"]
ADAFRUIT_IO_FEEDNAME = credentials["ADAFRUIT_IO_FEEDNAME"]

random_num = int.from_bytes(os.urandom(3), 'little')
mqtt_client_id = bytes('client_'+str(random_num), 'utf-8')

c = MQTTClient(client_id=mqtt_client_id,
                    server=ADAFRUIT_IO_URL,
                    user=ADAFRUIT_USERNAME,
                    password=ADAFRUIT_IO_KEY,
                    ssl=False)
c.DEBUG = False # Print diagnostic messages when retries/reconnects happens
c.KEEP_QOS0 = False # Information whether we store unsent messages with the flag QoS==0 in the queue.
c.NO_QUEUE_DUPS = True # Option, limits the possibility of only one unique message being queued.
c.MSG_QUEUE_MAX = 2 # Limit the number of unsent messages in the queue.
c.set_callback(sub_cb)

mqtt_feedname = '{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME)

if not c.connect(clean_session=False):
    print("Klapper kameller til Adafruit IO og sender bananer, med klient ID: ",random_num)
    c.subscribe(mqtt_feedname)
