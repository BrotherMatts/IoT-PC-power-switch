import network
from time import sleep_ms
from machine import Pin
from umqtt.simple import MQTTClient
import secrets as s

################################################
#  TODO:
#    1. Separate connectivity from app-class
#    2. Implement state checking (input from reset switch?)
#    3. Implement force off (TESTING)
#    4. Implement ARGB power led
#    5. Implement secrets as class rather than forced global variables
################################################

# Below import & install needs to be run the first time.
# import upip
# upip.install('umqtt.simple')

class App:

    # Init
    def __init__(self,
                wifi_ssid=s.wifi_ssid,
                wifi_pass=s.wifi_pass,
                ):
        
        # Init HW pins & LED. Pin.off() is called to allow low output value later. Does nothing on input.
        self.led = led = Pin("LED", Pin.OUT)
        self.pwr_pin = Pin(2, Pin.IN, Pin.PULL_UP)
        self.pwr_pin.off()
        print(self.pwr_pin)
        
        # Init connections to WIFI and MQTT broker.
        # TODO: Seaprate connections to own classes and implement reconnection possibilities
        self.wlan = self.wlan_conn(wifi_ssid, wifi_pass)
        print("WLAN initialized: " + str(self.wlan))
        self.mqtt_cli = self.mqtt_conn()
        print("MQTT initialized: " + str(self.mqtt_cli))
        
        # Helper variables
        self.got_msg = False
        self.first_round = True
    ####

    # WLAN connection function
    def wlan_conn(self, ssid, pass_):

        # Display wifi status
        tf = False # Used to blink LED while connecting to WIFI
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
        
        # Connection established
        self.led.value(1)
        print("Connected succesfully!")
        return wlan
    ####
    
    # Callback for MQTT messages.
    # Basically means this function is called to power on the pc when command is received
    def sub_callback(self, mqtt_topic, mqtt_msg):
        print((mqtt_topic, mqtt_msg))
        if self.first_round:
            self.first_round = False
            if mqtt_msg == b'poweron':
                self.led.value(1)
            else:
                self.led.value(0)
            print("Skipping first message action")
            pass
        elif mqtt_topic == b'mqtt_pc':
            if mqtt_msg == b'poweron':
                try:
                    self.power_pc(200)
                    self.led.value(1)
                except:
                    self.pwr_pin.init(Pin.IN, Pin.PULL_UP)
                    self.led.value(0)
                    print("ERROR WHEN TRYING TO BOOT")
            elif mqtt_msg == b'poweroff':
                try:
                    self.power_pc(200)
                    self.led.value(0)
                except:
                    self.pwr_pin.init(Pin.IN, Pin.PULL_UP)
                    self.led.value(1)
                    print("ERROR WHEN TRYING TO SHUT")
            elif mqtt_msg == b'forceoff':
                try:
                    self.power_pc(4000)
                    self.led.value(0)
                except:
                    self.pwr_pin.init(Pin.IN, Pin.PULL_UP)
                    self.led.value(1)
                    print("ERROR WHEN TRYING TO SHUT")
        self.got_msg = True
    ####
    
    # Function to flick PWR pin with desired time (mode: 200 = normal press, 4000 = long press)
    def power_pc(self, mode):
        self.pwr_pin.init(Pin.OUT)
        print(self.pwr_pin, self.pwr_pin.value())
        sleep_ms(mode)
        self.pwr_pin.init(Pin.IN, Pin.PULL_UP)
        print(self.pwr_pin)
    
    # Establishing connection to MQTT broker
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
    
# Create app object
application = App()
application.led.value(0)
print("Setting LED off. From this point on LED corresponds with pc power status")
round_counter = 1

# logical infinite loop. "Main program"
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



