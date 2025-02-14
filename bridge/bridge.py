import speech_recognition as sr
import serial
import serial.tools.list_ports
import audio_processing as ap
import paho.mqtt.client as mqtt

import configparser

from enum import IntEnum, StrEnum, auto 
import time 

from datetime import *

import requests

class Command(IntEnum):
    AUTO_OFF = 0
    SWITCH_OFF = 2
    MOBILE_APP_OFF = 4
    VOICECOMMAND_OFF = 6
    RED_VOICE_HIGH = 8 
    RED_VOICE_MEDIUM = 9 
    RED_VOICE_LOW = 10 
    RED_MOBILE_APP_HIGH = 11 
    RED_MOBILE_APP_MEDIUM = 12 
    RED_MOBILE_APP_LOW = 13 
    RED_AUTO_HIGH = 14 
    RED_AUTO_MEDIUM = 15 
    RED_AUTO_LOW = 16 
    RED_SWITCH_HIGH = 17 
    RED_SWITCH_MEDIUM = 18 
    RED_SWITCH_LOW = 19 
    GREEN_VOICE_HIGH = 20 
    GREEN_VOICE_MEDIUM = 21 
    GREEN_VOICE_LOW = 22 
    GREEN_MOBILE_APP_HIGH = 23 
    GREEN_MOBILE_APP_MEDIUM = 24 
    GREEN_MOBILE_APP_LOW = 25 
    GREEN_AUTO_HIGH = 26 
    GREEN_AUTO_MEDIUM = 27 
    GREEN_AUTO_LOW = 28 
    GREEN_SWITCH_HIGH = 29 
    GREEN_SWITCH_MEDIUM = 30 
    GREEN_SWITCH_LOW = 31 
    BLUE_VOICE_HIGH = 32 
    BLUE_VOICE_MEDIUM = 33 
    BLUE_VOICE_LOW = 34 
    BLUE_MOBILE_APP_HIGH = 35 
    BLUE_MOBILE_APP_MEDIUM = 36 
    BLUE_MOBILE_APP_LOW = 37 
    BLUE_AUTO_HIGH = 38 
    BLUE_AUTO_MEDIUM = 39 
    BLUE_AUTO_LOW = 40 
    BLUE_SWITCH_HIGH = 41 
    BLUE_SWITCH_MEDIUM = 42 
    BLUE_SWITCH_LOW = 43 
    YELLOW_VOICE_HIGH = 44 
    YELLOW_VOICE_MEDIUM = 45 
    YELLOW_VOICE_LOW = 46 
    YELLOW_MOBILE_APP_HIGH = 47 
    YELLOW_MOBILE_APP_MEDIUM = 48 
    YELLOW_MOBILE_APP_LOW = 49 
    YELLOW_AUTO_HIGH = 50 
    YELLOW_AUTO_MEDIUM = 51 
    YELLOW_AUTO_LOW = 52 
    YELLOW_SWITCH_HIGH = 53 
    YELLOW_SWITCH_MEDIUM = 54 
    YELLOW_SWITCH_LOW = 55 
    PURPLE_VOICE_HIGH = 56 
    PURPLE_VOICE_MEDIUM = 57
    PURPLE_VOICE_LOW = 58
    PURPLE_MOBILE_APP_HIGH = 59
    PURPLE_MOBILE_APP_MEDIUM = 60
    PURPLE_MOBILE_APP_LOW = 61
    PURPLE_AUTO_HIGH = 62
    PURPLE_AUTO_MEDIUM = 63
    PURPLE_AUTO_LOW = 64
    PURPLE_SWITCH_HIGH = 65
    PURPLE_SWITCH_MEDIUM = 66
    PURPLE_SWITCH_LOW = 67
    PINK_VOICE_HIGH = 68
    PINK_VOICE_MEDIUM = 69
    PINK_VOICE_LOW = 70
    PINK_MOBILE_APP_HIGH = 71
    PINK_MOBILE_APP_MEDIUM = 72
    PINK_MOBILE_APP_LOW = 73
    PINK_AUTO_HIGH = 74
    PINK_AUTO_MEDIUM = 75
    PINK_AUTO_LOW = 76
    PINK_SWITCH_HIGH = 77
    PINK_SWITCH_MEDIUM = 78
    PINK_SWITCH_LOW = 79
    ORANGE_VOICE_HIGH = 80
    ORANGE_VOICE_MEDIUM = 81
    ORANGE_VOICE_LOW = 82
    ORANGE_MOBILE_APP_HIGH = 83
    ORANGE_MOBILE_APP_MEDIUM = 84
    ORANGE_MOBILE_APP_LOW = 85
    ORANGE_AUTO_HIGH = 86
    ORANGE_AUTO_MEDIUM = 87
    ORANGE_AUTO_LOW = 88
    ORANGE_SWITCH_HIGH = 89
    ORANGE_SWITCH_MEDIUM = 90
    ORANGE_SWITCH_LOW = 91
    WHITE_VOICE_HIGH = 92
    WHITE_VOICE_MEDIUM = 93
    WHITE_VOICE_LOW = 94
    WHITE_MOBILE_APP_HIGH = 95
    WHITE_MOBILE_APP_MEDIUM = 96
    WHITE_MOBILE_APP_LOW = 97
    WHITE_AUTO_HIGH = 98
    WHITE_AUTO_MEDIUM = 99
    WHITE_AUTO_LOW = 100
    WHITE_SWITCH_HIGH = 101
    WHITE_SWITCH_MEDIUM = 102
    WHITE_SWITCH_LOW = 103

class Type(IntEnum):
    OFF = 0
    ON = 1

class Mode(StrEnum):
    AUTO = auto()
    SWITCH = auto()
    MOBILE_APP = 'mobile app'
    VOICE = auto()

class Color(StrEnum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    YELLOW = auto()
    PURPLE = auto()
    PINK = auto()
    ORANGE = auto()
    WHITE = auto()

class LightIntensity(StrEnum):
    HIGH = auto() 
    MEDIUM = auto() 
    LOW = auto()

class Event(IntEnum):
    BUILD_PACKET = 0 # HTTP
    START_TIMER = 1 # HTTP
    PEOPLE_IN_THE_ROOM = 2 # MQTT
    BUILD_PACKET_AND_START_TIMER = 3



    

class Packet():
    def __init__(self, timestamp: datetime, username: str, duration: float, on_mode: Mode, off_mode: Mode, color: Color, light_intensity: LightIntensity, power_consumption: float):
        self.timestamp = timestamp
        self.username = username
        self.duration = duration 
        self.on_mode = on_mode
        self.off_mode = off_mode
        self.color = color 
        self.light_intensity = light_intensity
        self.power_consumption = power_consumption
    
    def to_dict(self):
        return {
            'timestamp': str(self.timestamp),
            'username': self.username,
            'duration': self.duration,
            'on mode': str(self.on_mode),
            'off mode': str(self.off_mode),
            'color': str(self.color),
            'light intensity': str(self.light_intensity),
            'power consumption': self.power_consumption
        }

class Bridge():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.pubtopic = self.config.get("MQTT","PubTopic", fallback= "user")

        self.recognizer = sr.Recognizer()
        self.last_int_message = int(Command.AUTO_OFF)
        self.timer: datetime
        self.people_in_the_room = 0
        self.auto_mode = 'enabled'

        self.packet = Packet(None, 'Saverio', None, None, None, None, None, None)

        self.setup_serial()
        self.setup_mqtt()
    
    def setup_serial(self):
        # open serial port
        self.ser = None

        if not self.config.getboolean("Serial","UseDescription", fallback=False):
            self.portname = self.config.get("Serial","PortName", fallback="/dev/cu.usbserial-0001")
        else:
            print("list of available ports: ")
            ports = serial.tools.list_ports.comports()

            for port in ports:
                print (port.device)
                print (port.description)
                if self.config.get("Serial","PortDescription", fallback="arduino").lower() \
                        in port.description.lower():
                    self.portname = port.device

        try:
            if self.portname is not None:
                print ("connecting to " + self.portname)
                self.ser = serial.Serial(self.portname, 9600, timeout=0)
        except:
            self.ser = None
            print("Cannot connect to " + self.portname)
    
    def setup_mqtt(self):
        self.client_mqtt = mqtt.Client()
        self.client_mqtt.on_connect = self.on_connect
        self.client_mqtt.on_message = self.on_message
        print("Connecting to MQTT broker...")
        self.client_mqtt.connect(
            self.config.get("MQTT","Server", fallback= "localhost"),
            self.config.getint("MQTT","Port", fallback= 1883),
            60)

        self.client_mqtt.loop_start()

    
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        topics = [self.config.get("MQTT","SubTopicBedroomLight", fallback= "mobileapp/bedroom/light"), self.config.get("MQTT","SubTopicBathroomLight", fallback= "mobileapp/bathroom/light"),
        self.config.get("MQTT","SubTopicLivingRoomLight", fallback= "mobileapp/livingroom/light"), self.config.get("MQTT","SubTopicKitchenLight", fallback= "mobileapp/kitchen/light")]
        self.client_mqtt.subscribe([(t, 0) for t in topics])
        print("Subscribed to " + str(topics))

    # The callback for when a PUBLISH message is received from the server.
    # User sends input from mobile app
    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        if msg.topic == self.config.get("MQTT","SubTopicLivingRoomLight", fallback= "mobileapp/livingroom/light"):
            if msg.payload == b'state': # mobile app asking for current state
                    if self.evaluate_message(self.last_int_message, Type.ON):
                        color = self.get_color(self.last_int_message)
                        intensity = self.get_light_intensity(self.last_int_message)
                        self.client_mqtt.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "home/livingroom/light"), f'{str(color)} {str(intensity)}')
                    if self.evaluate_message(self.last_int_message, Type.OFF):
                        self.client_mqtt.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "home/livingroom/light"), 'off')
                    
                    self.client_mqtt.publish(self.config.get("MQTT","PubTopicLivingRoomPeople", fallback="home/livingroom/people"), f'{self.people_in_the_room}')
                    self.client_mqtt.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "home/livingroom/light"), f'{str(self.auto_mode)}')

            elif not self.ser is None:
                # we add a 1 at the end to tell the micro it was a command sent by the mobile app
                if msg.payload == b'on' or msg.payload == b'white high':
                    msg.payload = b'255,255,255,1'
                if msg.payload == b'white low':
                    msg.payload = b'8,8,8,1'
                if msg.payload == b'white medium':
                    msg.payload == b'64,64,64,1'
                if msg.payload == b'off':
                    msg.payload = b'0,0,0,1'
                if msg.payload == b'red high':
                    msg.payload = b'255,0,0,1'
                if msg.payload == b'red low':
                    msg.payload = b'8,0,0,1'
                if msg.payload == b'red medium':
                    msg.payload = b'64,0,0,1'
                if msg.payload == b'green high':
                    msg.payload = b'0,255,0,1'
                if msg.payload == b'green low':
                    msg.payload = b'0,8,0,1'
                if msg.payload == b'green medium':
                    msg.payload = b'0,64,0,1'
                if msg.payload == b'blue high':
                    msg.payload = b'0,0,255,1'
                if msg.payload == b'blue low':
                    msg.payload = b'0,0,8,1'
                if msg.payload == b'blue medium':
                    msg.payload = b'0,0,64,1'
                if msg.payload == b'yellow high':
                    msg.payload = b'255,255,0,1'
                if msg.payload == b'yellow low':
                    msg.payload = b'8,8,0,1'
                if msg.payload == b'yellow medium':
                    msg.payload = b'64,64,0,1'
                if msg.payload == b'orange high':
                    msg.payload = b'255,128,0,1'
                if msg.payload == b'orange low':
                    msg.payload = b'8,4,0,1'
                if msg.payload == b'orange medium':
                    msg.payload = b'64,32,0,1'
                if msg.payload == b'purple high':
                    msg.payload = b'127,0,255,1'
                if msg.payload == b'purple low':
                    msg.payload = b'4,0,8,1'
                if msg.payload == b'purple medium':
                    msg.payload = b'32,0,64,1'
                if msg.payload == b'pink high':
                    msg.payload = b'255,0,127,1'
                if msg.payload == b'pink low':
                    msg.payload = b'8,0,4,1'
                if msg.payload == b'pink medium':
                    msg.payload = b'64,0,32,1'
                if msg.payload == b'auto':
                    msg.payload = b'-1'
                if msg.payload == b'not auto':
                    msg.payload = b'-2'

                msg.payload = msg.payload + b'\n'
                print(str(msg.payload))
                self.ser.write(msg.payload)
                
    
    def execute_audio_command(self, recognizer, audio):
        text = ap.convert_voice_to_text(audio)
        #print(text)
        command = ap.process_voice_commands(text)
        #print(command)
        if command is not None:
            #print("I'm sending the command")
            self.ser.write(command)
    
    def loop(self):
        while True:
            if self.ser is not None:
                if self.ser.in_waiting > 0:
                    byte_message = self.ser.read(1)
                    int_message = int.from_bytes(byte_message)
                    if int_message <= 103:
                        print(f'Received message {int_message} from the micro')
                        self.use_message(int_message)
                        #print('Call useMessage')
                    else:
                        if int_message == 238:
                            self.auto_mode = 'enabled'
                        elif int_message == 239:
                            self.auto_mode = 'disabled'
                        else:
                            people_in_the_room = int.from_bytes(self.ser.read(1))
                            self.people_in_the_room = people_in_the_room
                            self.notify_subscribers(Event.PEOPLE_IN_THE_ROOM, people_in_the_room)

    
    def use_message(self, int_message: int):
        event: Event = None #TODO understand why sometimes the ifs below are not executed

        if self.has_to_build_packet_and_start_timer(int_message):
            self.build_packet(int_message)
            self.send_packet()
            self.timer = datetime.now()
            event = Event.BUILD_PACKET_AND_START_TIMER
            self.last_int_message = int_message
        elif self.has_to_build_packet(int_message):
            self.build_packet(int_message)
            event = Event.BUILD_PACKET
            self.send_packet()
            self.last_int_message = int_message
        elif self.has_to_start_timer(int_message):
            self.timer = datetime.now()
            self.packet.color = self.get_color(int_message)
            self.packet.light_intensity = self.get_light_intensity(int_message)
            self.packet.on_mode = self.get_on_mode(int_message)
                
            event = Event.START_TIMER
            self.last_int_message = int_message

        if event is not None:
            self.notify_subscribers(event, int_message)
        
    def evaluate_message(self, message: int, message_type: Type):
        if message is not None:
            if message_type == Type.OFF:
                return 0 <= message <= 6 and message % 2 == 0 
            if message_type == Type.ON:
                return 8 <= message <= 103
        else:
            return False 
        
    
    def has_to_build_packet(self, int_message: int):
        return self.evaluate_message(self.last_int_message, Type.ON) and self.evaluate_message(int_message, Type.OFF) # ON -> OFF
    
    def has_to_start_timer(self, int_message: int):
        return self.evaluate_message(self.last_int_message, Type.OFF) and self.evaluate_message(int_message, Type.ON) # OFF -> ON
    
    def has_to_build_packet_and_start_timer(self, int_message: int):
        if self.evaluate_message(self.last_int_message, Type.ON) and self.evaluate_message(int_message, Type.ON): # ON -> ON
            # OLD COLOR != NEW COLOR OR OLD LIGHT INTENSiTY != NEW LIGHT INTENSiTY
            return self.get_color(self.last_int_message) != self.get_color(int_message) or self.get_light_intensity(self.last_int_message) != self.get_light_intensity(int_message)
        return False 

    def build_packet(self, int_message: int):
        print('building packet')
        print(f'last message: {self.last_int_message}')
        print(f'current message: {int_message}')
        price = 0.15 #TODO set price
        self.packet.timestamp = datetime.now()
        self.packet.duration = (self.packet.timestamp-self.timer).total_seconds()
        self.packet.off_mode = self.getOffMode(int_message)
        self.packet.power_consumption = self.packet.duration * price
        
    # Send packet to the rest server
    def send_packet(self):
        requests.post(self.config.get('HTTP', 'URL', fallback='http://127.0.0.1/bridge'), json=self.packet.to_dict(), headers={'Content-type': 'application/json'})
        #print('sending packet')

    # Notify mobile app and server that something has changed
    def notify_subscribers(self, event: Event, message: int):
        if event == Event.BUILD_PACKET: # message has to be off    
            self.client_mqtt.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "home/livingroom/light"), 'off')
        if event == Event.START_TIMER or event == Event.BUILD_PACKET_AND_START_TIMER: # message has to be on
            color = self.get_color(message)
            intensity = self.get_light_intensity(message)
            self.client_mqtt.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "home/livingroom/light"), f'{str(color)} {str(intensity)}')
        if event == Event.PEOPLE_IN_THE_ROOM:
            self.client_mqtt.publish(self.config.get("MQTT","PubTopicLivingRoomPeople", fallback= "home/livingroom/people"), f'{message}')
        
    
    def get_color(self, message: int) -> Color:
        if 8 <= message <= 19:
            return Color.RED
        if 20 <= message <= 31:
            return Color.GREEN
        if 32 <= message <= 43:
            return Color.BLUE
        if 44 <= message <= 55:
            return Color.YELLOW
        if 56 <= message <= 67:
            return Color.PURPLE
        if 68 <= message <= 79:
            return Color.PINK 
        if 80 <= message <= 91:
            return Color.ORANGE
        if 92 <= message <= 103:
            return Color.WHITE
    
    def get_on_mode(self, message: int) -> Mode:
        
        if 8 <= message <= 10 or 20 <= message <= 22 or 32 <= message <= 34 or 44 <= message <= 46 or 56 <= message <= 58 or 68 <= message <= 70 or 80 <= message <= 82 or 92 <= message <= 94:  
            return Mode.VOICE
        
        if 11 <= message <= 13 or 23 <= message <= 25 or 35 <= message <= 37 or 47 <= message <= 49 or 59 <= message <= 61 or 71 <= message <= 73 or 83 <= message <= 85 or 95 <= message <= 97:
            return Mode.MOBILE_APP
        
        if 14 <= message <= 16 or 26 <= message <= 28 or 38 <= message <= 40 or 50 <= message <= 52 or 62 <= message <= 64 or 74 <= message <= 76 or 86 <= message <= 88 or 98 <= message <= 100:
            return Mode.AUTO
        
        return Mode.SWITCH
    
    def getOffMode(self, message: int) -> Mode:
        if message == 0:
            return Mode.AUTO
        if message == 2:
            return Mode.SWITCH
        if message == 4:
            return Mode.MOBILE_APP
        if message == 6:
            return Mode.VOICE
    
    def get_light_intensity(self, message: int) -> LightIntensity:
        if message == 8 or message == 11 or message == 14 or message == 17 or message == 20 or message == 23 or message == 26 or message == 29 or message == 32 or message == 35 or message == 38 or message == 41 or message == 44 or message == 47 or message == 50 or message == 53 or message == 56 or message == 59 or message == 62 or message == 65 or message == 68 or message == 71 or message == 74 or message == 77 or message == 80 or message == 83 or message == 86 or message == 89 or message == 92 or message == 95 or message == 98 or message == 101:
            return LightIntensity.HIGH
        if message == 9 or message == 12 or message == 15 or message == 18 or message == 21 or message == 24 or message == 27 or message == 30 or message == 33 or message == 36 or message == 39 or message == 42 or message == 45 or message == 48 or message == 51 or message == 54 or message == 57 or message == 60 or message == 63 or message == 66 or message == 69 or message == 72 or message == 75 or message == 78 or message == 81 or message == 84 or message == 87 or message == 90 or message == 93 or message == 96 or message == 99 or message == 102:
            return LightIntensity.MEDIUM
        
        return LightIntensity.LOW

def main():
    recognizer = sr.Recognizer()
    br = Bridge()
    recognizer.listen_in_background(sr.Microphone(), br.execute_audio_command)
    br.loop()

main()
    
