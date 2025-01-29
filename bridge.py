import speech_recognition as sr
import serial
import serial.tools.list_ports
import audio_processing as ap

import configparser

from enum import IntEnum, StrEnum 
import time 

from datetime import *

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


    

class Packet():
    def __init__(self, timestamp: datetime, duration: float, on_mode: Mode, off_mode: Mode, color: Color, color_mode: Mode, light_intensity: LightIntensity, power_consumption: float):
        self.timestamp = timestamp
        self.duration = duration 
        self.on_mode = on_mode
        self.off_mode = off_mode
        self.color = color 
        self.color_mode = color_mode
        self.light_intensity = light_intensity
        self.power_consumption = power_consumption





class Bridge():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.pubtopic = self.config.get("MQTT","PubTopic", fallback= "sensor")

        self.recognizer = sr.Recognizer()
        self.last_int_message: int
        self.timer_start: datetime

        self.packet = Packet(None, None, None, None, None, None, None, None)

        self.setupSerial()
        self.setupMQTT()
    
    def setupSerial(self):
        # open serial port
        self.ser = None

        if not self.config.getboolean("Serial","UseDescription", fallback=False):
            self.portname = self.config.get("Serial","PortName", fallback="COM1")
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
        t = self.config.get("MQTT","SubTopic", fallback= "mylight")
        
        self.clientMQTT.subscribe(t)
        print("Subscribed to " + t)
        #TODO handle multiple subtopics

    # The callback for when a PUBLISH message is received from the server.
    # User sends input from mobile app
    # TODO bridge subscribed to topic 'user' and publishes to topic 'home', mobile_app subscribed to topic 'home' and publishes to topic 'user' 
    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        if msg.topic == self.config.get("MQTT","SubTopic", fallback= "mylight"):
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
                    msg.payload = b'65\n'
                if msg.payload == b'NOT AUTO' or msg.payload == b'Not Auto' or msg.payload == b'not auto':
                    msg.payload = b'66\n'
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
                        self.useMessage(int_message)
                    elif int_message :
                        self.notify_subscribers(Event.PEOPLE_IN_THE_ROOM, int_message)

            self.execute_audio_command()
    
    def useMessage(self, int_message: int):
        event: Event
        if self.hasToBuildPacket(int_message):
            self.buildPacket(int_message)
            event = Event.BUILD_PACKET
            self.sendPacket(packet)
            self.last_int_message = int_message
        if self.hasToStartTimer(int_message):
            self.timer_start = datetime.now()
            if self.evaluateMessage(int_message, Type.COLOR):
                self.packet.color = self.findColor(int_message)
                self.packet.color_mode = self.findColorMode(int_message)
                self.packet.light_intensity = LightIntensity.HIGH
            if self.evaluateMessage(int_message, Type.ON):
                self.packet.on_mode = self.findOnMode(int_message)
                self.packet.color = Color.WHITE
                self.packet.color_mode = self.packet.on_mode
                self.packet.light_intensity = LightIntensity.HIGH
            if self.evaluateMessage(int_message, Type.LIGHT_INTENSITY):
                self.packet.light_intensity = self.findLightIntensity(int_message)
                self.packet.color = Color.WHITE
                self.packet.on_mode = Mode.AUTO
                self.packet.color_mode = self.packet.on_mode
                
            event = Event.TIMER_START
            self.last_int_message = int_message

        self.notify_subscribers(event)
        
    def evaluateMessage(self, message: int, message_type: Type):
        if message_type == Type.OFF:
            return 0 <= message <= 7 and message % 2 == 0 
        if message_type == Type.ON:
            return 0 <= message <= 7 and message % 2 > 0
        if message_type == Type.COLOR:
            return 8 <= message <= 21
        if message_type == Type.LIGHT_INTENSITY:
            return message == LightIntensity.HIGH or message == LightIntensity.MEDIUM or message == LightIntensity.LOW
    
    def hasToBuildPacket(self, int_message: int):
        return (self.evaluateMessage(int_message, Type.OFF) and self.evaluateMessage(self.last_int_message, Type.ON)) or (self.evaluateMessage(int_message, Type.COLOR) and self.evaluateMessage(self.last_int_message, Type.ON)) or (self.evaluateMessage(int_message, Type.OFF) and self.evaluateMessage(self.last_int_message, Type.COLOR)) or (self.evaluateMessage(int_message, Type.COLOR) and self.evaluateMessage(self.last_int_message, Type.COLOR)) or (self.evaluateMessage(int_message, Type.LIGHT_INTENSITY) and self.evaluateMessage(self.last_int_message, Type.LIGHT_INTENSITY)) or (self.evaluateMessage(int_message, Type.OFF) and self.evaluateMessage(self.last_int_message, Type.LIGHT_INTENSITY)) or (self.evaluateMessage(int_message, Type.COLOR) and self.evaluateMessage(self.last_int_message, Type.LIGHT_INTENSITY)) or (self.evaluateMessage(int_message, Type.LIGHT_INTENSITY) and self.evaluateMessage(self.last_int_message, Type.ON))
    
    def hasToStartTimer(self, int_message: int):
        return (self.evaluateMessage(int_message, Type.ON) and self.evaluateMessage(self.last_int_message, Type.OFF)) or (self.evaluateMessage(int_message, Type.COLOR) and self.evaluateMessage(self.last_int_message, Type.OFF)) or (self.evaluateMessage(int_message, Type.LIGHT_INTENSITY) and self.evaluateMessage(self.last_int_message, Type.OFF))

    def buildPacket(self, int_message: int):
        price = ...
        self.packet.timestamp = datetime.now()
        self.packet.duration = (timestamp-self.timer_start).total_seconds()
        self.packet.off_mode = self.findOffMode(int_message)
        self.packet.power_consumption = duration * price
        
    # Send packet to the rest server
    def sendPacket(self, packet: Packet):
        pass


    # Notify mobile app that something has changed
    def notify_subscribers(self, event: Event, message: int):
        if event == Event.BUILD_PACKET:
            if self.evaluateMessage(message, Type.OFF):
                self.clientMQTT.publish(self.config.get("MQTT","PubTopic", fallback= "mylight")+'/{:d}'.format(i), 'light off')
            if self.evaluateMessage(message, Type.COLOR):
                color = self.findColor(message)
                self.clientMQTT.publish(self.config.get("MQTT","PubTopic", fallback= "mylight")+'/{:d}'.format(i), f'color changed to {str(color)}')
        if event == Event.TIMER_START:
            if self.evaluateMessage(message, Type.ON):
                self.clientMQTT.publish(self.config.get("MQTT","PubTopic", fallback= "mylight")+'/{:d}'.format(i), 'light on')
            if self.evaluateMessage(message, Type.COLOR):
                color = self.findColor(message)
                self.clientMQTT.publish(self.config.get("MQTT","PubTopic", fallback= "mylight")+'/{:d}'.format(i), f'color changed to {str(color)}')
        if event == Event.PEOPLE_IN_THE_ROOM:
            self.clientMQTT.publish(self.config.get("MQTT","PubTopic", fallback= "mylight")+'/{:d}'.format(i), f'{message} people in the room')
    
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
    
