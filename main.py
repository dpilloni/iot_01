import mqtt_simple_v2 as mqtt #MQTT modul og script til wifi samt adafruit forbindelse
import features as feat #henter teatures.py ind, som indeholder de fleste funktioner vi bruger
import time #henter hele Time modulet ind
from machine import Pin, ADC, Timer #importere Pin, ADC funktion from Machine modul

timeLastToggle = 0 #tid's log til "time.ticks_diff" functionen
battery_pin = ADC(Pin(34)) #henter ADC sinal fra pin 34, som bruges til at aflæse volt fra batteri
battery_pin.atten(ADC.ATTN_11DB) #fuld bredte 3.3v
battery_pin.width(ADC.WIDTH_10BIT) #sætter bit resolution til 10 = (2^10) - 1 == range(0 - 1023)

puls = ADC(Pin(32)) #henter ADC sinal fra puls måleren
puls.atten(ADC.ATTN_11DB) #fuld bredte 3.3v
puls.width(ADC.WIDTH_10BIT) #sætter bit resolution til 10 = (2^10) - 1 == range(0 - 1023)

max_pulse_items = 400 #max antal af items i listen: pulse_data[] 
pulse_data = [] #liste til at holde puls data
bpm_list = []
beat_status = False #boolean til kun at få ét puls 
beats = 0 #puls tal

class status(): #status klassen indeholder variabler omkring systemet.
    wifi_conn = False #boolean om der er wifi
    ada_conn = False #boolean om der er forbindelse til adafruit/MQTT
    sleep_counter = 0 #en sleep variable

class player_data(): #klasse om spiller data
    batteri = 3.8 #variable til batteri volt
    tacklinger = 0 #variable til antal tacklinger
    puls = 0 #variable til puls 
    counter = 0 #variable til counter
    gps = "" #variable til GPS data fra gps modul
    speed = 0 #variable til speed
    play_tackled = False #boolean til tackling  
    play_down = False #boolean til om spiller er oppe eller nede

btn1 = Pin(4, Pin.IN) #variable til knap
bt_val_1 = 0 #variable til knap værdig

feat.np_tacklinger(0,"off") #nulstiller NeoPixel

def get_battery_volt(): #function til at få batteri målen
    total = 0 #variable spænding (v)
    
    for i in range(64): #looper i 64 gange og tager 64 målinger af batteriet.
        total = total + battery_pin.read()
    
    total = total >> 6 #rykker bit 6 gange og derved forbi gennemsnittet af de 64 målinger
    
    return (total / 220 ) #retunere volt værdien i skalerert tilstand faktor = 899/4.1

    
pulse_ADC = 0 #variable til ADC værdien af pulsmåler

def timer_puls(t): #Timer function til at måle bpm (beats per minute)
    global beats #sætter beats variable til global så den kan ændres
    global bpm_list 
    bpm_per_min = int(beats * 4) # player_data.puls = BPM * 6,
    bpm_list.append(bpm_per_min)
    bpm_list = bpm_list[-10:]
    
    calc_bpm = 0
    
    for bpm_val in bpm_list:
        calc_bpm += int(bpm_val)    
    
    player_data.puls = int(calc_bpm / len(bpm_list))  
    print(player_data.puls)
    beats = 0 #nulstiller beats

#indstiller timer til at kalde funktionen timer_puls hvert 10 sek.
beat_timer = Timer(1)
beat_timer.init(period=15000, mode=Timer.PERIODIC, callback=timer_puls)  

while True: #main loop
        
    if time.ticks_diff(time.ticks_ms(), timeLastToggle) > 100: # hvis tiden siden sisdte 
        
        try: #try, except til fejlhåndtering    
            #puls censor, henter data, calibere ved at finder mindste og max værdig:
            pulse_ADC = puls.read() #læser ADC værdig fra puls censor
            pulse_data.append(pulse_ADC) #indsætter pulsmåling i listen puls_data 
            pulse_data = pulse_data[-max_pulse_items:] # ændre lænngden af listen til at
                                                       # indeholde de sidste 200 målinger
            min_p = min(pulse_data) #finder den mindste måling i listen: pulse_data
            max_p = max(pulse_data) #finder den størreste måling i listen: pulse_data
            
            threshold_on = (min_p + max_p * 2.5) // 4 # finder threshold for hvornår pulsen er høj.
                                                    # svare til en 3/4 af max værdien. 
            threshold_off = (min_p + max_p) // 2    # finder threshold for hvornår pulsen er lav.
                                                    # svare til 1/2 af max værdien
                                                    #
                                                    # dobbelt dividering (//) = laver resultattet
                                                    # om til integer værdi.
            
            if beat_status==False and pulse_ADC > threshold_on: #registere puls går op
                 beat_status = True #sætter boolean til true
                 beats += 1 
                 
            if beat_status==True and pulse_ADC < threshold_off: #registere at pulsen på ned, hvis
                                                                #den har været oppe.
                beat_status = False
 
            acc_z = feat.gyro_meter("acc_z") #henter gyroscope data på z akslen
            acc_x = feat.gyro_meter("acc_x") #henter gyroscope data på x akslen
            
            gyro_value = feat.gyro_meter("down") #henter accelerometer data x akslen
            if gyro_value < 60: #hvis x akslen er under 60 sætter den play_down = true
                player_data.play_down = True 
            else:
                player_data.play_down = False
                
            if acc_z > 1500 or acc_z < -1500 or acc_x > 1500 or acc_x < -1500:
                #registre hvis der voldsomme udsving på x eller z aklsen, hvilket svare til
                #en skulder tackling
                
                if player_data.play_down == False: #hvis spilleren får en skulder tackling er den
                                                   #skal den registeret hvis han står op.
                    player_data.play_tackled = True
            else:
                player_data.play_tackled = False
            
            #if elif case for hvornår en spilleren er tacklet
            
            if player_data.play_tackled == True and player_data.play_down == False:
                player_data.counter = player_data.counter + 1
                #player_data.counter bliver brugt til at registere antal tacklinger
                
            elif player_data.play_tackled == False and player_data.play_down == True:
                player_data.counter = player_data.counter + 1
            
            elif player_data.play_down == False:
                player_data.counter = 0 
                #Hvis spilleren ikke er nede sættes player_data.counter til 0, så den er klar
                #til at registrere tacklinger 
            
            if player_data.counter == 1: 
                player_data.tacklinger = player_data.tacklinger + 1
                feat.np_tacklinger(player_data.tacklinger,"on")
            
            #knap registering
            bt_val_1 = btn1.value()
            
            if bt_val_1 == 0: #hvis trykkes ned viser neopixel batteri status, wifi status og mqtt status
                feat.np_light(player_data.batteri, status.wifi_conn, status.ada_conn)
            else: #ellers viser den antal tacklinger   
                feat.np_tacklinger(player_data.tacklinger,"on")
            
            if mqtt.status_wifi() == True and mqtt.status_ada() == False:
                status.ada_conn = True
            
            if mqtt.status_wifi() == True:
                status.wifi_conn = True          
                mqtt.sync_with_adafruitIO()            
            else:
                mqtt.connect_2_wifi()
            
            if status.ada_conn == True and status.wifi_conn == True:
                status.sleep_counter = status.sleep_counter + 1
                
                if status.sleep_counter > 55:
                    player_data.speed = feat.get_gps("speed")
                    player_data.gps = feat.get_gps("position")
                    batteri_pro = ( (get_battery_volt() -3.7) / 1.2) * 100            
                    
                    mqtt.sync_with_adafruitIO() 
                    mqtt.sent_MQTT(batteri_pro, "batteri")
                    mqtt.sent_MQTT(player_data.puls, "Puls")
                    mqtt.sent_MQTT(player_data.tacklinger, "tacklinger")
                    mqtt.sent_MQTT(player_data.gps, "position/csv")
                    mqtt.sent_MQTT(player_data.speed, "hastighed")
                    mqtt.sent_MQTT("Connected", "connect")
                    mqtt.sent_MQTT("1", "Ping")
                    status.sleep_counter = 0
                    

            timeLastToggle = time.ticks_ms()
            
        except KeyboardInterrupt: # Stopper programmet når der trykkes Ctrl + c
            print('Ctrl-C pressed...exiting')
            mqtt.c.disconnect()
            mqtt.sys.exit()