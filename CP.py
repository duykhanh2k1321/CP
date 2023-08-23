import sys
import signal
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
reading = True
default_pin_len = 6
default_pin = "      "
pin_input = default_pin

''' Define keypads '''
KEYPAD = [ [1, 2, 3, "A"], [4, 5, 6, "B"], [7, 8, 9, "C"], ["*", 0, "#", "D"] ]
ROW_PINS = [14, 15, 18, 23] # BCM numbering
COL_PINS = [24, 25,  7,  1] # BCM numbering

''' Cleanup function when the program is terminated '''
def cleanup():
    global reading
    print("")
    print("Ctr+C captured, exiting")
    print("Cleaning up GPIO before exiting")
    print("")
    GPIO.cleanup()
    reading = False
    sys.exit()

''' Initialize pins and rfid reader '''
def setup():
    global reader
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(th1, GPIO.OUT, initial = 0)
    GPIO.setup(th2, GPIO.OUT, initial = 0)
    GPIO.setup(th3, GPIO.OUT, initial = 1)
    GPIO.setup(th4, GPIO.OUT, initial = 0)
    reader = SimpleMFRC522()
    
''' Initializes keypad driver '''
def init_keypad_driver():
    factory = rpi_gpio.KeypadFactory()
    keypad = factory.create_keypad(keypad=KEYPAD,row_pins=ROW_PINS, col_pins=COL_PINS) 
    keypad.registerKeyPressHandler()

''' Reset outputs '''
def reset_outputs():
    print("Reset outputs")
    print("")
    GPIO.output(th1, 0)
    GPIO.output(th2, 0)
    GPIO.output(th3, 1)
    GPIO.output(th4, 0)
    
''' Make beep_sound_1 '''    
def beep1():
    GPIO.output(th1, 1)
    print("th1 on")
    sleep(0.2)
    GPIO.ouput(th1, 0)
    print("th2 off")
    print("")
    
''' Make beep_sound_2 '''    
def beep2():
    for i in range (1, 5):
        GPIO.output(th2, 1)
        print("th2 on")
        sleep(0.05)
        GPIO.output(th2, 0)
        print("th2 off")
        print("")
        sleep(0.05)
    
''' Valid rfid_input/pin_input '''
def valid_info():
    print("Valid rfid_input/pin_input")
    print("Pass level 1 security")
    print("")
    reset_outputs()
    beep1()
    reset_outputs()
    
''' Invalid rfid_input/pin_input '''
def invalid_info():
    print("Invalid rfid_input/pin_input")
    print("Not pass level 1 security")
    print("")
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
    print("")
    GPIO.output(th3, 1)
    GPIO.output(th4, 0)
    reset_outputs()

''' Scan rfid '''
def scan_rfid():
    print("Scan RFID card/tag")
    rfid_input, _ = reader.read()
    print(f"RFID: {rfid_input}")
    print("Do not scan RFID card/tag")
    print("Connecting to REST API Server")
    print("Checking RFID")
    sleep (1)
    rfid_error, rfid_recieve = rfid_check(rfid_input)
    if rfid_error:
        return
    if rfid_recieve:
        valid_info()
        print(f"Info: {rfid_recieve}")
        print("")
    else:
        invalid_info()

''' Get rfid data '''        
def rfid_check(rfid_input):
    rfid_error = False
    try:
        rfid_recieve = requests.post(url, json = {"rfid_data": rfid_input}, timeout = 5)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print("")
        rfid_error = True
        return rfid_error, False
    return rfid_error, rfid_recieve.json()

def main():
    global reader
    setup()
    while reading:
        scan_rfid()
            
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
