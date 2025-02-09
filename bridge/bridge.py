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
    AUTO_ON = 1
    SWITCH_OFF = 2
    SWITCH_ON = 3
    USER_OFF = 4
    USER_ON = 5
    VOICECOMMAND_OFF = 6
    VOICECOMMAND_ON = 7
    RED_VOICE = 8
    RED_USER = 9
    GREEN_VOICE = 10
    GREEN_USER = 11
    BLUE_VOICE = 12
    BLUE_USER = 13
    YELLOW_VOICE = 14
    YELLOW_USER = 15
    PURPLE_VOICE = 16
    PURPLE_USER = 17
    PINK_VOICE = 18
    PINK_USER = 19
    ORANGE_VOICE = 20
    ORANGE_USER = 21

class Type(IntEnum):
    OFF = 0
    ON = 1
    COLOR = 2
    LIGHT_INTENSITY = 3

class Mode(StrEnum):
    AUTO = auto()
    SWITCH = auto()
    USER = auto()
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

class LightIntensity(IntEnum):
    HIGH = 255 
    MEDIUM = 175 
    LOW = 100

class Event(IntEnum):
    BUILD_PACKET = 0
    TIMER_START = 1
    PEOPLE_IN_THE_ROOM = 2
    BUILD_PACKET_AND_TIMER_START = 3


    

class Packet():
    def __init__(self, timestamp: datetime, username: str, duration: float, on_mode: Mode, off_mode: Mode, color: Color, color_mode: Mode, light_intensity: LightIntensity, power_consumption: float):
        self.timestamp = timestamp
        self.username = username
        self.duration = duration 
        self.on_mode = on_mode
        self.off_mode = off_mode
        self.color = color 
        self.color_mode = color_mode
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
            'color mode': str(self.color_mode),
            'light intensity': int(self.light_intensity),
            'power consumption': self.power_consumption
        }





class Bridge():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.pubtopic = self.config.get("MQTT","PubTopic", fallback= "user")

        self.recognizer = sr.Recognizer()
        self.last_int_message: int
        self.timer_start: datetime

        self.packet = Packet(None, 'Saverio', None, None, None, None, None, None, None)
        self.last_int_message = None

        self.setupSerial()
        self.setupMQTT()
    
    def setupSerial(self):
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
        
        self.inbuffer = []
    
    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        self.clientMQTT.on_message = self.on_message
        print("Connecting to MQTT broker...")
        self.clientMQTT.connect(
            self.config.get("MQTT","Server", fallback= "localhost"),
            self.config.getint("MQTT","Port", fallback= 1883),
            60)

        self.clientMQTT.loop_start()

    
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        topics = [self.config.get("MQTT","SubTopicBedroomLight", fallback= "home"), self.config.get("MQTT","SubTopicBathroomLight", fallback= "home"),
        self.config.get("MQTT","SubTopicLivingRoomLight", fallback= "home"), self.config.get("MQTT","SubTopicKitchenLight", fallback= "home")]
        self.clientMQTT.subscribe([(t, 0) for t in topics])
        print("Subscribed to " + str(topics))

    # The callback for when a PUBLISH message is received from the server.
    # User sends input from mobile app
    #TODO refactor to handle multiple subtopics 
    # TODO bridge subscribed to topic 'user' and publishes to topic 'home', mobile_app subscribed to topic 'home' and publishes to topic 'user' 
    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        if msg.topic == self.config.get("MQTT","SubTopicLivingRoomLight", fallback= "home"):
            if not self.ser is None:
                # we add a 1 at the end to tell the micro it was a command sent by the mobile app
                if msg.payload == b'ON' or msg.payload == b'On' or msg.payload == b'on':
                    msg.payload = b'255,255,255,1\n'
                if msg.payload == b'OFF' or msg.payload == b'Off' or msg.payload == b'off':
                    msg.payload = b'0,0,0,1\n'
                if msg.payload == b'RED' or msg.payload == b'Red' or msg.payload == b'red':
                    msg.payload = b'255,0,0,1\n'
                if msg.payload == b'GREEN' or msg.payload == b'Green' or msg.payload == b'green':
                    msg.payload = b'0,255,0,1\n'
                if msg.payload == b'BLUE' or msg.payload == b'Blue' or msg.payload == b'blue':
                    msg.payload = b'0,0,255,1\n'
                if msg.payload == b'YELLOW' or msg.payload == b'Yellow' or msg.payload == b'yellow':
                    msg.payload = b'255,255,0,1\n'
                if msg.payload == b'ORANGE' or msg.payload == b'Orange' or msg.payload == b'orange':
                    msg.payload = b'255,128,0,1\n'
                if msg.payload == b'PURPLE' or msg.payload == b'Purple' or msg.payload == b'purple':
                    msg.payload = b'127,0,255,1\n'
                if msg.payload == b'PINK' or msg.payload == b'Pink' or msg.payload == b'pink':
                    msg.payload = b'255,0,127,1\n'
                if msg.payload == b'AUTO' or msg.payload == b'Auto' or msg.payload == b'auto':
                    msg.payload = b'-1\n'
                if msg.payload == b'NOT AUTO' or msg.payload == b'Not Auto' or msg.payload == b'not auto':
                    msg.payload = b'-2\n'
                print(str(msg.payload))
                self.ser.write(msg.payload)
        
    
    def execute_audio_command(self):
        audio = ap.capture_voice_input()
        text = ap.convert_voice_to_text(audio)
        command = ap.process_voice_commands(text)
        print(command)
        if command is not None:
            #print("I'm sending the command")
            self.ser.write(command)
    
    def loop(self):
        while True:
            if self.ser is not None:
                if self.ser.in_waiting > 0:
                    byte_message = self.ser.read(1)
                    int_message = int.from_bytes(byte_message)
                    if int_message <= 21:
                        print(f'Received message {int_message} from the micro')
                        self.useMessage(int_message)
                        #print('Call useMessage')
                    elif int_message:
                        people_in_the_room = int.from_bytes(self.ser.read(1))
                        self.notify_subscribers(Event.PEOPLE_IN_THE_ROOM, people_in_the_room)

            #self.execute_audio_command()
    
    def useMessage(self, int_message: int):
        event = Event.TIMER_START #TODO understand why sometimes the ifs below are not executed

        if self.hasToBuildPacketAndStartTimer(int_message):
            self.buildPacket(int_message)
            self.sendPacket()
            self.timer_start = datetime.now()
            event = event.BUILD_PACKET_AND_TIMER_START
            self.last_int_message = int_message
        elif self.hasToBuildPacket(int_message):
            self.buildPacket(int_message)
            event = Event.BUILD_PACKET
            self.sendPacket(self.packet)
            self.last_int_message = int_message
        elif self.hasToStartTimer(int_message):
            self.timer_start = datetime.now()
            if self.evaluateMessage(int_message, Type.COLOR): # If a COLOR is picked then the intensity is HIGH
                self.packet.color = self.findColor(int_message)
                self.packet.color_mode = self.findColorMode(int_message)
                self.packet.light_intensity = LightIntensity.HIGH
            if self.evaluateMessage(int_message, Type.ON): # If a light is turned ON then the COLOR is WHITE and the intensity is HIGH 
                self.packet.on_mode = self.findOnMode(int_message)
                self.packet.color = Color.WHITE
                self.packet.color_mode = self.packet.on_mode
                self.packet.light_intensity = LightIntensity.HIGH
            if self.evaluateMessage(int_message, Type.LIGHT_INTENSITY): # If LIGHT INTENISTY changes then the light is WHITE and the mode is AUTO
                self.packet.light_intensity = self.findLightIntensity(int_message)
                self.packet.color = Color.WHITE
                self.packet.on_mode = Mode.AUTO
                self.packet.color_mode = self.packet.on_mode
                
            event = Event.TIMER_START
            self.last_int_message = int_message

        self.notify_subscribers(event, int_message)
        
    def evaluateMessage(self, message: int, message_type: Type):
        if message is not None:
            if message_type == Type.OFF:
                return 0 <= message <= 7 and message % 2 == 0 
            if message_type == Type.ON:
                return 0 <= message <= 7 and message % 2 > 0
            if message_type == Type.COLOR:
                return 8 <= message <= 21
            if message_type == Type.LIGHT_INTENSITY:
                return message == LightIntensity.HIGH or message == LightIntensity.MEDIUM or message == LightIntensity.LOW
        else:
            return False 
        
    
    def hasToBuildPacket(self, int_message: int):
        if self.evaluateMessage(self.last_int_message, Type.ON) and self.evaluateMessage(int_message, Type.OFF): # ON -> OFF
            return True
        if self.evaluateMessage(self.last_int_message, Type.COLOR) and self.evaluateMessage(int_message, Type.OFF): # COLOR -> OFF
            return True
        if self.evaluateMessage(self.last_int_message, Type.LIGHT_INTENSITY) and self.evaluateMessage(int_message, Type.OFF): # LIGHT INTENSITY -> OFF
            return True 
        if self.evaluateMessage(self.last_int_message, Type.ON) and self.evaluateMessage(int_message, Type.LIGHT_INTENSITY): # ON -> LIGHT INTENSITY
            return True

        return False
    
    def hasToStartTimer(self, int_message: int):
        if self.evaluateMessage(self.last_int_message, Type.OFF) and self.evaluateMessage(int_message, Type.ON): # OFF -> ON
            return True 
        if self.evaluateMessage(self.last_int_message, Type.OFF) and self.evaluateMessage(int_message, Type.COLOR): # OFF -> COLOR 
            return True 
        if self.evaluateMessage(self.last_int_message, Type.OFF) and self.evaluateMessage(int_message, Type.LIGHT_INTENSITY): # OFF -> LIGHT INTENSITY
            return True 
        if self.last_int_message is None:
            return True

        return False
    
    def hasToBuildPacketAndStartTimer(self, int_message: int):
        if self.evaluateMessage(self.last_int_message, Type.COLOR) and self.evaluateMessage(int_message, Type.COLOR): # COLOR -> COLOR
            if self.findColor(self.last_int_message) != self.findColor(int_message): # OLD COLOR != NEW COLOR
                return True 
        if self.evaluateMessage(self.last_int_message, Type.ON) and self.evaluateMessage(int_message, Type.COLOR): # ON -> COLOR
            return True 
        if self.evaluateMessage(self.last_int_message, Type.LIGHT_INTENSITY) and self.evaluateMessage(int_message, Type.LIGHT_INTENSITY): # LIGHT INTENSITY -> LIGHT INTENISTY
            if self.findLightIntensity(self.last_int_message) != self.findLightIntensity(int_message): # OLD LIGHT INTENSiTY != NEW LIGHT INTENSiTY
                return True
        if self.evaluateMessage(self.last_int_message, Type.LIGHT_INTENSITY) and self.evaluateMessage(int_message, Type.COLOR): # LIGHT INTENSITY -> COLOR
            return True 
        
        return False 
        
        
        

    def buildPacket(self, int_message: int):
        print('building packet')
        print(f'last message: {self.last_int_message}')
        print(f'current message: {int_message}')
        price = 0.15 #TODO set price
        self.packet.timestamp = datetime.now()
        self.packet.duration = (self.packet.timestamp-self.timer_start).total_seconds()
        self.packet.off_mode = self.findOffMode(int_message)
        self.packet.power_consumption = self.packet.duration * price
        
    # Send packet to the rest server
    def sendPacket(self):
        requests.post(self.config.get('HTTP', 'URL', fallback='http://127.0.0.1:5000/bridge'), json=self.packet.to_dict(), headers={'Content-type': 'application/json'})
        #print('sending packet')

    # Notify mobile app and server that something has changed
    #TODO refactor multiple pubtopics
    def notify_subscribers(self, event: Event, message: int):
        if event == Event.BUILD_PACKET:
            if self.evaluateMessage(message, Type.OFF):
                self.clientMQTT.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "user"), 'off')
            if self.evaluateMessage(message, Type.COLOR):
                color = self.findColor(message)
                self.clientMQTT.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "user"), f'{str(color)}')
        if event == Event.TIMER_START:
            if self.evaluateMessage(message, Type.ON):
                self.clientMQTT.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "user"), 'on')
            if self.evaluateMessage(message, Type.COLOR):
                color = self.findColor(message)
                self.clientMQTT.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "user"), f'{str(color)}')
        if event == Event.PEOPLE_IN_THE_ROOM:
            #self.clientMQTT.publish(self.config.get("MQTT","PubTopicLivingRoomPeople", fallback= "user"), f'{message}')
            print('people in the room')
        if event == Event.BUILD_PACKET_AND_TIMER_START:
            if self.evaluateMessage(message, Type.COLOR):
                color = self.findColor(message)
                self.clientMQTT.publish(self.config.get("MQTT","PubTopicLivingRoomLight", fallback= "user"), f'{str(color)}')

    
    def findColor(self, message: int):
        if 8 <= message <= 9:
            return Color.RED
        if 10 <= message <= 11:
            return Color.GREEN
        if 12 <= message <= 13:
            return Color.BLUE
        if 14 <= message <= 15:
            return Color.YELLOW
        if 16 <= message <= 17:
            return Color.PURPLE
        if 18 <= message <= 19:
            return Color.PINK 
        if 20 <= message <= 21:
            return Color.ORANGE
    
    def findColorMode(self, message: int):
        return Mode.USER if message % 2 > 0 else Mode.VOICE
    
    def findOnMode(self, message: int):
        if message == 1:
            return Mode.AUTO
        if message == 3:
            return Mode.SWITCH
        if message == 5:
            return Mode.USER
        if message == 7:
            return Mode.VOICE
    
    def findOffMode(self, message: int):
        if message == 0:
            return Mode.AUTO
        if message == 2:
            return Mode.SWITCH
        if message == 4:
            return Mode.USER
        if message == 6:
            return Mode.VOICE
    
    def findLightIntensity(self, message: int):
        if LightIntensity.MEDIUM < message <= LightIntensity.HIGH:
            return LightIntensity.HIGH
        if LightIntensity.LOW < message <= LightIntensity.MEDIUM:
            return LightIntensity.MEDIUM
        if 0 < message <= LightIntensity.LOW:
            return LightIntensity.LOW




def main():
    br = Bridge()
    br.loop()

main()
    
