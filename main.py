import network
from time import sleep_ms
from machine import Pin
from umqtt.simple import MQTTClient
import secrets as s

# Below import & install needs to be run the first time.
# import upip
# upip.install('umqtt.simple')

################################################
#  TODO:
#    1. Separate connectivity from app-class - Done
#    2. Implement state checking (input from reset switch?)
#    3. Implement force off (TESTING)
#    4. Implement ARGB power led -- TESTING WS2811
#    5. Implement secrets as class rather than forced global variables
################################################

# class to hold pins
class Pin_Purse:
    def __init__(self):
        self.led_pin = Pin("LED", Pin.OUT)
        self.pwr_pin = Pin(2, Pin.IN, Pin.PULL_UP)
        self.pwr_pin.off() # Used to set OUTPUT value to LOW later
        print(self.pwr_pin)

    # Simple 1/0 function
    def set_light(self, val):
        self.led_pin.value(val)

    # Sets the pwr pin value accordingly
    def set_pwr_pin_value(self, value="IN"):
        if value == "IN":
            self.pwr_pin.init(Pin.IN, Pin.PULL_UP)
        elif value == "OUT":
            self.pwr_pin.init(Pin.OUT)
        else:
            pass


# Wifi object
# Modified code to allow reconnection
class WiFi_Object:
    def __init__(self,
                led_pin,
                wifi_ssid=s.wifi_ssid,
                wifi_pass=s.wifi_pass):
        self.connection_base = self.connect_base(wifi_ssid, wifi_pass)
        self.connection, self.conn_status = self.conn(led_pin)
        #self.connection_base = None
    
    def connect_base(self, ssid, pass_):
        # Conn status
        status = True

        # Display wifi status
        tf = False # Used to blink LED while connecting to WIFI

        # wlan connection params
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(ssid, pass_)

        return wlan

    def conn(self, led_pin):
        if self.conn_status:
            return self.connection, self.conn_status
        else:
            status = True
            rounds = 0
            while not self.connection_base.isconnected():
                tf = not tf
                if tf:
                    led_pin.set_light(1)
                else:
                    led_pin.set_light(0)
                print("Connecting...")
                sleep_ms(100)
                rounds += 1

                # Stopping infinite connecting
                if rounds == 100:
                    led_pin.set_light(0)
                    status = False
                    self.connection_base.active(False)
                    print("Stopping connecting, 100 rounds reached without succesful connection.")
                    return self.connection_base, status
                    break
            
            # Connection established
            led_pin.set_light(1)
            print("Connected succesfully!")
            return self.connection_base, status

class MQTT_Object:
        
    def __init__(self):
        self.mqtt_cli = self.mqtt_conn()
        self.first_round = True
        self.got_msg = False
        print("MQTT initialized: " + str(self.mqtt_cli))

    def reset_got_msg(self):
        self.got_msg = False

    # connect to MQTT broker and subscribe to topic
    def mqtt_conn   (self,
                    mqtt_server = s.mqtt_server,
                    mqtt_port = s.mqtt_port,
                    mqtt_user = s.mqtt_user,
                    mqtt_pass = s.mqtt_pass,
                    mqtt_client = s.mqtt_client,
                    mqtt_topic = s.mqtt_topic,
                    mqtt_msg = s.mqtt_msg):
        client = MQTTClient(mqtt_client, mqtt_server, mqtt_port, mqtt_user, mqtt_pass, keepalive=3600)
        client.set_callback(self.sub_callback) # Callback function to be called every time a message is received
        client.connect()
        client.subscribe("mqtt_pc")
        return client

    # Callback for MQTT messages.
    # Basically means this function is called to power on the pc when command is received
    def sub_callback(self, mqtt_topic, mqtt_msg, led_pin, pin_purse):
        print((mqtt_topic, mqtt_msg))
        if self.first_round:
            self.first_round = False
            if mqtt_msg == b'poweron':
                led_pin.set_light(1)
            else:
                led_pin.set_light(0)
            print("Skipping first message action")
            pass
        elif mqtt_topic == b'mqtt_pc':
            if mqtt_msg == b'poweron':
                try:
                    self.power_pc(200)
                    led_pin.set_light(1)
                except:
                    self.pwr_pin.init(Pin.IN, Pin.PULL_UP)
                    led_pin.set_light(0)
                    print("ERROR WHEN TRYING TO BOOT")
            elif mqtt_msg == b'poweroff':
                try:
                    self.power_pc(200)
                    led_pin.set_light(0)
                except:
                    self.pwr_pin.init(Pin.IN, Pin.PULL_UP)
                    led_pin.set_light(1)
                    print("ERROR WHEN TRYING TO SHUT")
            elif mqtt_msg == b'forceoff':
                try:
                    self.power_pc(4000)
                    led_pin.set_light(0)
                except:
                    self.pwr_pin.init(Pin.IN, Pin.PULL_UP)
                    led_pin.set_light(1)
                    print("ERROR WHEN TRYING TO SHUT")
        self.got_msg = True

    # Function to flick PWR pin with desired time (mode: 200 = normal press, 4000 = long press)
    def power_pc(self, mode, pin_purse):
        pin_purse.set_pwr_pin_value("OUT")
        print(pin_purse.pwr_pin)
        sleep_ms(mode)
        pin_purse.set_pwr_pin_value("IN")
        print(pin_purse.pwr_pin)

class Wrapper:
    def __init__(self):
        self.pins = Pin_Purse()
        self.wifi = WiFi_Object(self.pins.led_pin)
        self.mqtt = MQTT_Object()
    
    def publish(self):
        self.mqtt.publish(b"mqtt_pc_conn", b"Yo! I'm still here")

    def reset_got_msg(self):
        self.mqtt.reset_got_msg()
    
    def got_msg(self):
        return self.mqtt.got_msg

    def check_mqtt_msg(self):
        self.mqtt.check_msg()


# Create application core object
app = Wrapper()
round_counter = 0 # Used to renew MQTT
deep_sleep_counter = 0 # Used to allow deep sleep
# TODO:
    # Use RTC clock to allow deep sleep between 4am and 5pm

# logical infinite loop. "Main program"
while True:
    app.check_mqtt_msg()
    if app.got_msg():
        round_counter = 0
        app.reset_got_msg()
    sleep_ms(5000)
    if round_counter == 100:
        if deep_sleep_counter == 100:
            # DO DEEP SLEEP
            pass
        app.publish() # Used to renew MQTT connection, not letting it die
        round_counter = 0
    round_counter += 1



