import sys
import json
import signal
import drivers
import requests
import RPi.GPIO as GPIO

from time import sleep
from pad4pi import rpi_gpio
from mfrc522 import SimpleMFRC522

''' api_url '''
url = ""

''' Define pins '''
''' th1: red_led_1 + buzzer, th2: green_led + buzzer, th3: red_led_2, th4: lock_control_block '''
th1 = 12 
th2 = 16
th3 = 20
th4 = 21

''' Define variables '''
reader = None
pin_input = default
default_pin_len = 6
default_pin = "      "

''' Define keypads '''
KEYPAD = [ [1, 2, 3, "A"], [4, 5, 6, "B"], [7, 8, 9, "C"], ["*", 0, "#", "D"] ]
ROW_PINS = [14, 15, 18, 23] # BCM numbering
COL_PINS = [24, 25,  7,  1] # BCM numbering

''' Setup RPi '''
GPIO.setwarnings(False)

''' Cleanup function when the program is terminated '''
def cleaup(signal, frame):
    print(" captured, exiting")
    print("Cleaning up GPIO before exiting")
    GPIO.cleanup()
    sys.exit()
    
''' Hook function when the program is terminated '''
signal.signal(signal.SIGINT, cleanup)

''' Initialize pins and rfid reader '''
def setup():
    global reader
    GPIO.setwarnings(False)
    reader = SimpleMFRC522()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(th1, GPIO.OUT, 0)
    GPIO.setup(th2, GPIO.OUT, 0)
    GPIO.setup(th3, GPIO.OUT, 1)
    GPIO.setup(th4, GPIO.OUT, 0)
    
''' Initializes keypad driver '''
def init_keypad_driver():
    factory = rpi_gpio.KeypadFactory()
    keypad = factory.create_keypad(keypad=KEYPAD,row_pins=ROW_PINS, col_pins=COL_PINS) 
    keypad.registerKeyPressHandler(handle_keypad_press, scan_rfid)

''' Reset outputs '''
def reset_outputs():
    print("Reset outputs")
    GPIO.output(th1, 0)
    GPIO.output(th2, 0)
    GPIO.output(th3, 1)
    GPIO.output(th4, 0)
    
''' Make beep_sound_1 '''    
def beep1():
    GPIO.setup(th1, GPIO.OUT, 1)
    print("th1 on")
    sleep(0.2)
    GPIO.setup(th1, GPIO.OUT, 0)
    print("th2 off")
    
''' Make beep_sound_2 '''    
def beep2():
    for i in range (1, 5):
        GPIO.output(th2, GPIO.OUT, 1)
        print("th2 on")
        sleep(0.05)
        GPIO.output(th2, GPIO.OUT, 0)
        print("th2 off")
        sleep(0.05)
    
''' Valid rfid_input/pin_input '''
def valid_info():
    print("Valid rfid_input/pin_input")
    print("Pass level 1 security")
    reset_outputs()
    beep1()
    reset_outputs()
    
''' Invalid rfid_input/pin_input '''
def invalid_info():
    print("Invalid rfid_input/pin_input")
    print("Not pass level 1 security")
    reset_outputs()
    beep2()
    reset_outputs()
    
''' Unlock and lock after 3 seconds '''
def latch():
    print("Unlocking")
    GPIO.output(th3, 0)
    GPIO.output(th4, 1)
    sleep(3)
    print("Locking")
    GPIO.output(th3, 1)
    GPIO.output(th4, 0)

''' Scan rfid '''
def scan_rfid():
    print("Scan RFID card/tag")
    rfid_input, _ = reader.read()
    print(f"RFID: {rfid_input}")
    print("Do not scan RFID card/tag")
    print("Connecting to REST API Server")
    print("Checking RFID")
    rfid_error, rfid_recieve = rfid_check(rfid_input)
    if rfid_error:
        return
    if rfid_recieve:
        valid_info()
        print(f"Info: {rfid_recieve}")
    else:
        invalid_info()
        
''' Scan keypad '''  
def scan_pin(press):
    global pin_input 
    if press == "*":
        print(f"{press}")
        print("Clearing input")
        pin_input = default_pin
        print(f"Input pin: {pin_input}")
    elif press == "#":
        if len(pin_input.strip()) < default_pin_len:
            print("Incomplete pin")
            print(f"Input pin: {pin_input}")
            return
        print("Connecting to REST API Server")
        print("Checking RFID")
        pin_error, pin_recieve = pin_check(pin_input)
        if pin_error:
            return
        if pin_recieve:
            valid_info()
            print(f"Info: {pin_recieve}")
            input_key_codes = DEFAULT_INDENT
            print(f"Input pin: {pin_input}")
        else:
            invalid_info()
            pin_input = default_pin
            print(f"Input pin: {pin_input}")
    else:
        if len(pin_input.strip()) == default_pin_len:
            print("Exceed limit")
            print(f"Input pin: {pin_input}")
            return
        pin_input += str(press)
        print(f"Input pin: {pin_input}")        
        
''' Get rfid data '''        
def rfid_check(rfid_input):
    rfid_error = False
    try:
        rfid_recieve = requests.post(API_URL, json = {"rfid_data": rfid_data}, timeout = 5)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        rfid_error = True
        return rfid_error, False
    return rfid_error, rfid_recieve.json()
        
''' Get pin data '''        
def pin_check(rfid_input):
    pin_error = False
    try:
        pin_recieve = requests.post(API_URL, json = {"pin_data": pin_data}, timeout = 5)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        pin_error = True
        return pin_error, False
    return pin_error, pin_recieve.json()