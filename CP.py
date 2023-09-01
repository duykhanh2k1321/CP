import sys
import signal
import requests
import RPi.GPIO as GPIO

from time import sleep
from pad4pi import rpi_gpio
from mfrc522 import SimpleMFRC522

''' api_url '''
url = 'https://a888-113-172-235-185.ngrok-free.app/api/hardware/check-for-l1'

''' Define pins '''
''' th1: red_led_1 + buzzer, th2: green_led + buzzer, th3: red_led_2, th4: lock_control_block '''
th1 = 12 
th2 = 16
th3 = 20
th4 = 21

''' Define variables '''
reader = None
pin_input = ''

''' Define keypads '''
KEYPAD = [[1, 2, 3, 'A'], [4, 5, 6, 'B'], [7, 8, 9, 'C'], ['*', 0, '#', 'D']]
ROW_PINS = [14, 15, 18, 23]
COL_PINS = [24, 25,  7,  1]

''' Cleanup function when the program is terminated '''
def cleanup():
    print('\nCtr+C captured, exiting')
    print('Cleaning up GPIO before exiting')
    GPIO.cleanup()
    pin_input = ''
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
    
''' Reset outputs '''
def reset_outputs():
    print('Reset outputs\n')
    GPIO.output(th1, 0)
    GPIO.output(th2, 0)
    GPIO.output(th3, 1)
    GPIO.output(th4, 0)
    
''' Make beep_sound_1 '''    
def beep1():
    GPIO.output(th1, 1)
    print('th1 on')
    print('Sleep 0.2')
    sleep(0.2)
    GPIO.output(th1, 0)
    print('th2 off')
    print('')
    
''' Make beep_sound_2 '''    
def beep2():
    for i in range (1, 5):
        GPIO.output(th2, 1)
        print('th2 on')
        print('Sleep 0.05')
        sleep(0.05)
        GPIO.output(th2, 0)
        print('th2 off')
        print('Sleep 0.05\n')
        sleep(0.05)
    
''' Valid rfid_input/pin_input '''
def valid_info():
    print('Valid RFID/PIN')
    print('Pass level 1 security\n')
    reset_outputs()
    beep1()
    reset_outputs()
    return main()
    
''' Invalid rfid_input/pin_input '''
def invalid_info():
    print('Invalid RFID/PIN')
    print('Not pass level 1 security\n')
    reset_outputs()
    beep2()
    reset_outputs()
    return main()
    
''' Unlock and lock after 3 seconds '''
def latch():
    print('Unlocking')
    print('Afetr 3 seconds')
    GPIO.output(th3, 0)
    GPIO.output(th4, 1)
    sleep(3)
    print('Locking\n')
    GPIO.output(th3, 1)
    GPIO.output(th4, 0)
    reset_outputs()

''' Initializes keypad driver '''
def keypad_0():
    global key_0
    factory = rpi_gpio.KeypadFactory()
    key_0 = factory.create_keypad(keypad=KEYPAD,row_pins=ROW_PINS, col_pins=COL_PINS) 
    key_0.registerKeyPressHandler(scan_in_out)

def keypad_1():
    global key_1
    factory = rpi_gpio.KeypadFactory()
    key_1 = factory.create_keypad(keypad=KEYPAD,row_pins=ROW_PINS, col_pins=COL_PINS) 
    key_1.registerKeyPressHandler(scan_rfid_pin)
    
def keypad_2():
    global key_2
    factory = rpi_gpio.KeypadFactory()
    key_2 = factory.create_keypad(keypad=KEYPAD,row_pins=ROW_PINS, col_pins=COL_PINS) 
    key_2.registerKeyPressHandler(scan_rfid)
    
def keypad_3():
    global key_3
    factory = rpi_gpio.KeypadFactory()
    key_3 = factory.create_keypad(keypad=KEYPAD,row_pins=ROW_PINS, col_pins=COL_PINS) 
    key_3.registerKeyPressHandler(scan_pin)
    
def clr_keypad_0():
    global key_0
    if key_0:
        key_0.unregisterKeyPressHandler(scan_in_out)
        key_0 = None

def clr_keypad_1():
    global key_1
    if key_1:
        key_1.unregisterKeyPressHandler(scan_rfid_pin)
        key_1 = None

def clr_keypad_2():
    global key_2
    if key_2:
        key_2.unregisterKeyPressHandler(scan_rfid)
        key_2 = None
        
def clr_keypad_3():
    global key_3
    if key_3:
        key_3.unregisterKeyPressHandler(scan_pin)
        key_3 = None

''' Scan rfid '''
def scan_rfid(press):
    if press == '*':
        print('Back to startup\n')
        sleep(0.5)
        GPIO.cleanup()
        setup()
        key = ''
        clr_keypad_2()
        return main()
    elif press == '#':
        print('Scan RFID card/tag\n')
        rfid_input, _ = reader.read()
        print(f'RFID: {rfid_input}')
        print('Do not scan RFID card/tag')
        print('Connecting to REST API Server')
        print('Checking RFID\n')
        sleep (1)
        rfid_error, rfid_recieve = rfid_check(rfid_input)
        if rfid_error:
            sleep(0.5)
            GPIO.cleanup()
            setup()
            key = ''
            clr_keypad_2()
            return main()
        if rfid_recieve:
            print(f'Info: {rfid_recieve.text}')
            sleep(0.5)
            GPIO.cleanup()
            setup()
            key = ''
            clr_keypad_2()
            valid_info()
        else:
            print(f'Info: {rfid_recieve.text}')
            sleep(0.5)
            GPIO.cleanup()
            setup()
            key = ''
            clr_keypad_2()
            invalid_info()
    else:
        pass

        
''' Get rfid data '''        
def rfid_check(rfid_input):
    rfid_error = False
    try:
        rfid_recieve = requests.post(url, json = {'rfid_data': rfid_input}, timeout = 5)
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}\n')
        rfid_error = True
        return rfid_error, False
    print(f'{rfid_recieve}\n')
    return rfid_error, rfid_recieve

''' Scan pin '''
def scan_pin(press):
    global pin_input
    if press == '*':
        pin_input = ''
        print('Clearing input')
        print('Back to startup\n')
        sleep(0.5)
        GPIO.cleanup()
        setup()
        key = ''
        clr_keypad_3()
        return main()
    elif press == '#':
        if len(pin_input.strip()) < 6:
            print('Incomplete PIN code')
            print('Continue inputing\n')
            sleep(0.2)
            return
        print('Connecting to REST API Server')
        print('Checking PIN\n')
        pin_error, pin_recieve = pin_check(pin_input)
        if pin_error:
            sleep(0.5)
            GPIO.cleanup()
            setup()
            key = ''
            clr_keypad_3()
            return main()
        if pin_recieve:
            pin_input = ''
            print(f'Info: {pin_recieve.text}')
            sleep(0.5)
            GPIO.cleanup()
            setup()
            key = ''
            clr_keypad_3()
            valid_info()
        else:
            pin_input = ''
            print(f'Info: {pin_recieve.text}')
            sleep(0.5)
            GPIO.cleanup()
            setup()
            key = ''
            clr_keypad_3()
            invalid_info()
    else:
        if len(pin_input.strip()) == 6:
            print('Exceed limitation')
            print(f'PIN input: {pin_input}')
            print('Press # for checking PIN info\n')
            sleep(0.2)
            return
        pin_input += str(press)
        print(f'PIN input: {pin_input}\n')
        sleep(0.5)

''' Get pin data '''        
def pin_check(pin_input):
    pin_error = False
    try:
        pin_recieve = requests.post(url, json = {'pin_code': pin_input}, timeout = 5)
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')
        print('')
        pin_error = True
        return pin_error, False
    print('{pin_recieve}\n')
    return pin_error, pin_recieve

def scan_in_out(press):
    if press == 'A':
        print('Access CHECKIN mode\n')
        sleep(0.5)
        GPIO.cleanup()
        setup()
        key = ''
        clr_keypad_0()
        main_rfid_pin()
    elif press == 'B':
        print('Access CHECKOUT mode\n')
        sleep(0.5)
        GPIO.cleanup()
        setup()
        key = ''
        clr_keypad_0()
        main_rfid_pin()
    else:
        pass
        
def scan_rfid_pin(press):
    if press == 'C':
        print('Access SCAN RDIF mode\n')
        GPIO.cleanup()
        setup()
        key = ''
        clr_keypad_1()
        main_rfid()
    elif press == 'D':
        print('Access SCAN PIN mode\n')
        GPIO.cleanup()
        setup()
        key = ''
        clr_keypad_1()
        main_pin()
    elif press == '*':
        print('Back to startup')
        print('')
        GPIO.cleanup()
        setup()
        key = ''
        clr_keypad_1()
        return main()
    else:
        pass

def main_rfid():
    global reader
    print('Press # then scan RFID tag/card - Press * to back to startup\n')
    keypad_2()
    while True:
        sleep(1)
        
def main_pin():
    print('Press # for checking PIN info - Press * to back to startup')
    print('Press keys to input PIN (except keys: A, B, C, D, #, *)\n')
    keypad_3()
    while True:
        sleep(1)
        
def main_in_out():
    keypad_0()
    while True:
        sleep(1)        
        
def main_rfid_pin():
    print('Choose mode: SCAN RFID - SCAN PIN')
    print('Press C for SCAN RFID mode - Press D for SCAN PIN mode - Press * to back to startup\n')
    keypad_1()
    while True:
        sleep(1)
        
def main():
    setup()
    print('Choose mode: CHECKIN - CHECKOUT')
    print('Press A for CHECKIN mode - Press B for CHECKOUT mode\n')
    main_in_out()
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
