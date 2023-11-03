#funktioner
import neopixel
from machine import Pin, I2C, UART #importere Pin, ADC funktion from Machine modul
from mpu6050 import MPU6050 # accelerometer gyrometer modul
from time import sleep #sleep 
from gps_bare_minimum import GPS_Minimum #gps modul

#sætter i2c for accelerometer/gyrometer
i2c = I2C(0) 
imu = MPU6050(i2c)

#GPS
gps_port = 2                               # ESP32 UART port, Educaboard ESP32 default UART port
gps_speed = 9600                           # UART speed, defauls u-blox speed
uart = UART(gps_port, gps_speed)           # UART object creation
gps = GPS_Minimum(uart) #uart data til GPS modul

class gps_data(): #klasse med gps data
    speed = 0
    lat = 0
    lon = 0    

def get_gps(spec): #gps modul, med et parameter "spec".
    if gps.receive_nmea_data():
        # hvis der er kommet end bruggbar værdi på alle der skal anvendes
        if gps.get_speed() != -999 and gps.get_latitude() != -999.0 and gps.get_longitude() != -999.0 and gps.get_validity() == "A":
            # gemmer returværdier fra metodekald i variabler
            gps_data.speed =str(gps.get_speed())
            gps_data.lat = str(gps.get_latitude())
            gps_data.lon = str(gps.get_longitude())
            # returnerer data med adafruit gps format
    if spec == "position": #hvis parameteret: spec er sat til position, retunere den GPS data 
        return str(gps_data.speed) + "," + str(gps_data.lat) + "," + str(gps_data.lon) + "," + "0.0"
    elif spec == "speed": #hvis parameteret: spec er sat til "speed", retunere den GPS kun speed
        return str(gps_data.speed)
    
def gyro_meter(cmd): #accelerometer/gyrometer function
    gyro_rate = 0
    gyro_x_val = 0
    gyro_result = 160
    try:
        gyro_data = imu.get_values() #få diratory med acceleration og gyro data
        
        if cmd == "acc_z":
            for i in range(10): #tager 10 målinger ved hvert 0.01 sek
                gyro_result += (int(gyro_data["gyroscope z"])/100) #dividere med 100, for at få et
                                                                   #mere brugbart tal
                sleep(0.01) #pause mellem målinger
        
        elif cmd == "acc_x":
            for i in range(10): #tager 10 målinger ved hvert 0.01 sek
                gyro_result += (int(gyro_data["gyroscope x"])/100) #dividere med 100, for at få et
                sleep(0.01) #pause mellem målinger                  mere brugbart tal
        
        elif cmd == "down":
            for i in range(10): #tager 10 målinger ved hvert 0.01 sek
                gyro_rate += int(gyro_data["acceleration x"]) #lægger målingerne sammen i gyro_rate variablen
                sleep(0.01) #pause mellem målinger
        
            gyro_result = int((gyro_rate/10)/100)  #divider med 10 og får gennemsnittet af målinger.
                                               #derefter divider vi med 100 for at få tallet ned
                                               #til et mere brugbart tal. er tallet under 100
                                               #er spilleren nede.
    except OSError: #håndtere gryo fejl
        None #gør intet ved fejl
        
    return gyro_result #retunere data

#neopixel
np = neopixel.NeoPixel(Pin(26), 12)

def np_tacklinger(no,cmd):
    for i in range(12): #nulstil neopixel
        np[i] = (0,0,0)

    color = "" #farve variable
    np_counter = 0 #tæller
    
    if no < 12: #tjekker om no er større eller ligmed 12, hvis ja så bliver den sat til 12
        color = (0,10,0) #sætter grøn farve
        np_counter = no
    elif no >= 12 and no < 24: #hvis større end 12 men mindre end 24
        color = (10,10,0) #sætter farven gul
        np_counter = no - 12 #trækker 12 fra counter, for at få det til at passe med antal
                             # RGB dioder i neopixel 
    elif no >= 24: #hvis større eller ligmed 24
        color = (10,0,0) #sætter farven til rød
        np_counter = no - 24
    else:
        np_counter = 12
    
    for i in range(12):
        if cmd == "on":
            if no < 12:        
                if i < np_counter:
                    np[i] = color
                else:
                    np[i] = (0,0,0)
            else:
                if i <= np_counter:
                    np[i] = color
                else:
                    np[i] = (0,0,0)
                
    np.write()

def np_light(batteri_val,wifi_stat,ada_stat):
    
    for i in range(12):
        np[i] = (0,00,0)
    
    calc_battery_pixels = int( ( (batteri_val-3) / 1.2) * 6) + 1
        
    if calc_battery_pixels < 12:
        for i in range(calc_battery_pixels): #sæt seks til at lyse som batteri indikator 
            np[i] = (0,50,0)
                    
        if wifi_stat == True:
            np[7] = (0,0,50)
        else:
            np[7] = (50,0,0)

        if ada_stat == True:
            np[10] = (0,0,50)
        else:
            np[10] = (50,0,0)
      
    np.write()


