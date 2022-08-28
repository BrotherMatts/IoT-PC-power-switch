import network
from time import sleep_ms
from machine import Pin
from umqtt.simple import MQTTClient
import secrets as s

dir(Pin)

# Below import & install needs to be run the first time.
# import upip
# upip.install('umqtt.simple')

class App:

    ####
    def __init__(self,
                wifi_ssid=s.wifi_ssid,
                wifi_pass=s.wifi_pass,
                ):
        self.led = led = Pin("LED", Pin.OUT)
        self.pwr_pin = Pin(2, Pin.IN, None)
        self.pwr_pin.off()
        print(self.pwr_pin)
        #self.pwr_pin = Pin(2, Pin.IN, Pin.PULL_DOWN)
        #print(self.pwr_pin)
        self.wlan = self.wlan_conn(wifi_ssid, wifi_pass)
        print("WLAN initialized: " + str(self.wlan))
        self.mqtt_cli = self.mqtt_conn()
        print("MQTT initialized: " + str(self.mqtt_cli))
        self.got_msg = False
        self.first_round = True
    ####

    ####
    def wlan_conn(self, ssid, pass_):

        # Display wifi status
        # self.led = Pin("LED", Pin.OUT)
        tf = False
        self.led.value(0)

        # wlan connection params
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(ssid, pass_)

        # Shows conn status
        while not wlan.isconnected():
            tf = not tf
            if tf:
                self.led.value(1)
            else:
                self.led.value(0)
            print("Connecting...")
            sleep_ms(100)
            
        self.led.value(1)
        print("Connected succesfully!")
        return wlan
    ####
    
    ####
    def sub_callback(self, mqtt_topic, mqtt_msg):
        print((mqtt_topic, mqtt_msg))
        if self.first_round:
            first_round = False
            pass
        elif mqtt_topic == b'mqtt_pc':
            if mqtt_msg == b'poweron':
                try:
                    self.power_pc("boot")
                    self.led.value(1)
                except:
                    self.pwr_pin.init(Pin.IN, None)
                    self.led.value(0)
                    print("ERROR WHEN TRYING TO BOOT")
            elif mqtt_msg == b'poweroff':
                try:
                    self.power_pc("boot")
                    self.led.value(0)
                except:
                    self.pwr_pin.init(Pin.IN, None)
                    self.led.value(1)
                    print("ERROR WHEN TRYING TO SHUT")
        self.got_msg = True
    ####
    
    def power_pc(self, mode):
        self.pwr_pin.init(Pin.OUT)
        print(self.pwr_pin, self.pwr_pin.value())
        sleep_ms(100)
        self.pwr_pin.init(Pin.IN, None)
        print(self.pwr_pin)
    
    ####
    def mqtt_conn   (self,
                    mqtt_server = s.mqtt_server,
                    mqtt_port = s.mqtt_port,
                    mqtt_user = s.mqtt_user,
                    mqtt_pass = s.mqtt_pass,
                    mqtt_client = s.mqtt_client,
                    mqtt_topic = s.mqtt_topic,
                    mqtt_msg = s.mqtt_msg):
        client = MQTTClient(mqtt_client, mqtt_server, mqtt_port, mqtt_user, mqtt_pass, keepalive=3600)
        client.set_callback(self.sub_callback)
        client.connect()
        client.subscribe("mqtt_pc")
        return client
    ####
    
application = App()
application.led.value(0)
print("Setting LED off. From this point on LED corresponds with pc power status")
round_counter = 1

while True:
    application.mqtt_cli.check_msg()
    print(application.got_msg)
    if application.got_msg:
        round_counter = 0
        application.got_msg = False
    sleep_ms(5000)
    if round_counter == 100:
        application.mqtt_cli.publish(b"mqtt_pc_conn", b"Yo! I'm still here")
        print("Kept connection alive by sending a message!")
        round_counter = 0
    round_counter += 1
    

        # # MQTT variables
        # mqtt_server = '192.168.178.46'
        # mqtt_port = 1883
        # mqtt_user = 'mqtt_svc_user'
        # mqtt_pass = 'mqtt_matti'
        # mqtt_client = 'core-mosquitto'
        # mqtt_topic = 'PC Power switch'
        # mqtt_msg = 'Change in val'



