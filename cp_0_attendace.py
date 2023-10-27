import os
import csv
import requests
import tkinter as tk
import RPi.GPIO as GPIO

from time import sleep
from time import strftime
from mfrc522 import SimpleMFRC522
from time import time as get_current_time

''' api_url '''
url = 'https://a888-113-172-235-185.ngrok-free.app/api/hardware/check-for-l1'

''' Define variables '''
reader = None
pin_input = ''

''' Define pins '''
''' th1: red_led_1 + buzzer, th2: green_led + buzzer, th3: red_led_2, th4: lock_control_block '''
th1 = 12 
th2 = 16
th3 = 20
th4 = 21

''' Define keypad buttons '''
keypad_buttons = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

''' Initialize pins and RFID reader '''
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
    
''' Valid RFID/PIN '''
def valid_data():
    print('Valid RFID/PIN')
    print('Pass level 1 security\n')
    reset_outputs()
    beep1()
    reset_outputs()
    
''' Invalid RFID/PIN '''
def invalid_data():
    print('Invalid RFID/PIN')
    print('Not pass level 1 security\n')
    reset_outputs()
    beep2()
    reset_outputs()
    
''' Error '''
def error():
    print('Error')
    print('Not pass level 1 security\n')
    reset_outputs()
    beep2()
    reset_outputs()
    
''' Unlock and lock after 3 seconds '''
def control_lock():
    print('Unlocking')
    print('Afetr 3 seconds')
    GPIO.output(th3, 0)
    GPIO.output(th4, 1)
    sleep(3)
    print('Locking\n')
    GPIO.output(th3, 1)
    GPIO.output(th4, 0)
    reset_outputs()

''' Check input data '''
''' Check RFID '''
def rfid_read():
    rfid_input, _ = reader.read()
    rfid_time = int(get_current_time())
    print(f'RFID: {rfid_input}')
    print(f'Time: {rfid_time}')
    print('Do not scan RFID card/tag')
    print('Connecting to REST API Server')
    print('Checking RFID\n')
    sleep (1)
    rfid_error, rfid_recieve = rfid_check(rfid_input)
    if rfid_error:
        print('NO CONNECTION TO API')
        if os.path.exists(f'{rfid_input}.csv'):
            with open(f'{rfid_input}.csv', 'a', newline = '') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow([rfid_time])
            print(f'Valid data: {rfid_input}')
            print('VALID page\n')
            rfid_input_page.pack_forget()
            valid_page.pack(expand = True, fill = 'both')
            win.after(1000, valid_data)
            win.after(2000, valid_to_face)
        else:
            print(f'Invalid: {rfid_input}')
            print('INVALID page\n')
            rfid_input_page.pack_forget()
            invalid_page.pack(expand = True, fill = 'both')
            win.after(1000, invalid_data)
            win.after(2000, invalid_to_main)
    elif rfid_recieve:
        print(f'Info:\n{rfid_recieve.text}')
        print('VALID page\n')
        rfid_input_page.pack_forget()
        valid_page.pack(expand = True, fill = 'both')
        win.after(1000, valid_data)
        win.after(2000, valid_to_face)
    else:       
        print(f'Info:\n{rfid_recieve.text}')
        print('INVALID page\n')
        rfid_input_page.pack_forget()
        invalid_page.pack(expand = True, fill = 'both')
        win.after(1000, invalid_data)
        win.after(2000, invalid_to_main)
        
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

''' Check PIN '''
def pin_read():
    global pin_input
    disable_buttons()
    print(f'Connecting to REST API Server to check PIN: {pin_input}\n')
    pin_error, pin_recieve = pin_check(pin_input)
    if pin_error:
        pin_input = ''
        pin_input_var.set('')
        print('ERROR page\n')
        pin_input_page.pack_forget()
        enable_buttons()
    elif pin_recieve:
        pin_input = ''
        pin_input_var.set('')
        print(f'Info:\n{pin_recieve.text}')
        print('VALID page\n')
        pin_input_page.pack_forget()
        enable_buttons()
        valid_page.pack(expand = True, fill = 'both')
        win.after(1000, valid_data)
        win.after(2000, valid_to_face)
    else:
        pin_input = ''
        pin_input_var.set('')
        print(f'Info:\n{pin_recieve.text}')
        print('INVALID page\n')
        pin_input_page.pack_forget()
        enable_buttons()
        invalid_page.pack(expand = True, fill = 'both')
        win.after(1000, invalid_data)
        win.after(2000, invalid_to_main)

def pin_check(pin_input):
    pin_error = False
    try:
        pin_recieve = requests.post(url, json = {'pin_code': pin_input}, timeout = 2)
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}\n')
        print('')
        pin_error = True
        return pin_error, False
    print('{pin_recieve}\n')
    return pin_error, pin_recieve

def main():
    setup()
    time()
    print('Level 1 Security\nMAIN page\n')
    main_page.pack(expand = True, fill = 'both')

def rfid():
    print('RFID page\n')
    main_page.pack_forget()
    rfid_page.pack(expand = True, fill = 'both')
    
def rfid_input():
    print('RFID INPUT page\nPlease input RFID card/tag\n')
    rfid_page.pack_forget()
    rfid_input_page.pack(expand = True, fill = 'both')
    win.after(100, rfid_read)
    
def rfid_to_main():
    print('RFID page to MAIN page\n')
    rfid_page.pack_forget()
    main()

def pin():
    print('PIN page\n')
    main_page.pack_forget()
    pin_page.pack(expand = True, fill = 'both')
    
def pin_input():
    print('PIN INPUT page\nPlease input PIN\n')
    pin_page.pack_forget()
    pin_input_page.pack(expand = True, fill = 'both')
    
def pin_to_main():
    print('PIN page to MAIN page\n')
    pin_page.pack_forget()
    main()

def pin_input_to_main():
    global pin_input
    pin_input = ''
    pin_input_var.set('')
    print(f'\nClear input PIN\nPIN INPUT page to MAIN page\n')
    pin_input_page.pack_forget()
    main()

def valid_to_face():
    print('VALID page to SCAN FACE page\n')
    valid_page.pack_forget()
    main()

def invalid_to_main():
    print('INVALID page to MAIN page\n')
    invalid_page.pack_forget()
    main()

def button_press(press):
    global pin_input
    pin_input = pin_input_var.get()
    if press == 'DELETE':
        if len(pin_input) > 0:
            pin_input_var.set(pin_input[:-1])
            print(f'PIN input: {pin_input[:-1]}')
    elif press == 'CHECK':
        if len(pin_input) == 6:
            print(f'\nChecking PIN input: {pin_input}\n')
            pin_read()
    elif len(pin_input) < 6:
        pin_input_var.set(pin_input + press)
        print(f'PIN input: {pin_input + press}')
        
def disable_buttons():
    for button in keypad.winfo_children():
        button.config(state='disabled')
    check.config(state='disabled')
    delete.config(state='disabled')
    back.config(state='disabled')

def enable_buttons():
    for button in keypad.winfo_children():
        button.config(state='normal')
    check.config(state='normal')
    delete.config(state='normal')
    back.config(state='normal')
   
def time():
    string = strftime('%A - %d/%m/%Y - %X')
    main_page_l0.config(text = string)
    rfid_page_l0.config(text = string)
    pin_page_l0.config(text = string)
    win.after(1000, time)
    
''' GUI window '''        
win = tk.Tk()

win = win
win.title('Attendance System')
win_wth = 1200
win_hht = 600
scr_wth = win.winfo_screenwidth()
scr_hht = win.winfo_screenheight()
x = (scr_wth/2) - (win_wth/2)
y = (scr_hht/2) - (win_hht/2)
win.geometry('%dx%d+%d+%d' % (win_wth, win_hht, x, y))

''' Choose mode RFID/PIN - MAIN page '''
main_page = tk.Frame(win)
main_page_l0 = tk.Label(main_page, font = ('arial', 50))
main_page_l0.pack()
main_page_l1 = tk.Label(main_page, text = 'LEVEL 1 SECURITY\nMAIN', font = ('arial', 50))
main_page_l1.pack()
main_page_l2 = tk.Button(main_page, text = 'RFID', font = ('arial', 50), bg = 'green', fg = 'white', command = rfid)
main_page_l2.pack(padx = 350, expand = True, fill = 'x')
main_page_l3 = tk.Button(main_page, text = 'PIN', font = ('arial', 50), bg = 'green', fg = 'white', command = pin)
main_page_l3.pack(padx = 350, expand = True, fill = 'x')

''' RFID page '''
rfid_page = tk.Frame(win)
rfid_page_l0 = tk.Label(rfid_page, font = ('arial', 50))
rfid_page_l0.pack()
rfid_page_l1 = tk.Label(rfid_page, text = 'LEVEL 1 SECURITY\nRFID', font = ('arial', 50))
rfid_page_l1.pack()
rfid_page_l2 = tk.Button(rfid_page, text = 'INPUT RFID', font = ('arial', 50), bg ='green', fg = 'white', command = rfid_input)
rfid_page_l2.pack(padx = 350, expand = True, fill = 'x')
rfid_page_l3 = tk.Button(rfid_page, text = 'BACK', font = ('arial', 50), bg = 'black', fg = 'white', command = rfid_to_main)
rfid_page_l3.pack(padx = 350, expand = True, fill = 'x')

''' RFID INPUT page '''
rfid_input_page = tk.Frame(win)
rfid_input_page_l0 = tk.Label(rfid_input_page, text = 'LEVEL 1 SECURITY\nRFID INPUT', font = ('arial', 50))
rfid_input_page_l0.pack()
rfid_input_page_l1 = tk.Label(rfid_input_page, text = 'PLEASE INPUT RFID CARD/TAG', font = ('arial', 50), bg ='green', fg = 'white')
rfid_input_page_l1.pack(expand = True)

''' PIN page '''
pin_page = tk.Frame(win)
pin_page_l0 = tk.Label(pin_page, font = ('arial', 50))
pin_page_l0.pack()
pin_page_l1 = tk.Label(pin_page, text = 'LEVEL 1 SECURITY\nPIN', font = ('arial', 50))
pin_page_l1.pack()
pin_page_l2 = tk.Button(pin_page, text = 'INPUT PIN', font = ('arial', 50), bg ='green', fg = 'white', command = pin_input)
pin_page_l2.pack(padx = 350, expand = True, fill = 'x')
pin_page_l3 = tk.Button(pin_page, text = 'BACK', font = ('arial', 50), bg = 'black', fg = 'white', command = pin_to_main)
pin_page_l3.pack(padx = 350, expand = True, fill = 'x')

''' PIN INPUT page '''
pin_input_page = tk.Frame(win)
pin_input_page_l0 = tk.Label(pin_input_page, text = 'LEVEL 1 SECURITY\nPIN INPUT', font = ('arial', 50))
pin_input_page_l0.pack()
pin_input_var = tk.StringVar()
pin_entry = tk.Entry(pin_input_page, font = ('arial', 50), width = 8, justify = 'center', textvariable = pin_input_var)
pin_entry.pack(expand = True)
keypad = tk.Frame(pin_input_page)
keypad.pack(expand = True)
for key in keypad_buttons:
    button = tk.Button(keypad, text = key, font = ('arial', 40), width = 3, height = 1, command = lambda press = key: button_press(press))
    button.grid(row = keypad_buttons.index(key)//5, column = keypad_buttons.index(key)%5)
button = tk.Frame(pin_input_page)
button.pack(expand = True)
check = tk.Button(button, text = 'CHECK', font = ('arial', 40), width = 8, height = 1, bg = 'green', fg = 'white', command = lambda: button_press('CHECK'))
check.pack(side = 'left', padx = 10)
delete = tk.Button(button, text = 'DELETE', font = ('arial', 40), width = 8, height = 1, bg = 'red', fg = 'white', command = lambda: button_press('DELETE'))
delete.pack(side = 'left', padx = 10)
back = tk.Button(button, text = 'BACK', font = ('arial', 40), width = 8, height = 1, bg = 'black', fg = 'white', command = pin_input_to_main)
back.pack(side = 'right', padx = 10)

''' VALID DATA page '''
valid_page = tk.Frame(win)
valid_page_l0 = tk.Label(valid_page, text = 'LEVEL 1 SECURITY\nVALID', font = ('arial', 50))
valid_page_l0.pack()
valid_page_l1 = tk.Label(valid_page, text = 'VALID DATA\nPASS LEVEL 1 SECURITY', font = ('arial', 50), bg ='green', fg = 'white')
valid_page_l1.pack(expand = True)

''' INVALID DATA page '''
invalid_page = tk.Frame(win)
invalid_page_l0 = tk.Label(invalid_page, text = 'LEVEL 1 SECURITY\nINVALID', font = ('arial', 50))
invalid_page_l0.pack()
invalid_page_l1 = tk.Label(invalid_page, text = 'INVALID DATA\nBACK TO MAIN WINDOW', font = ('arial', 50), bg ='red', fg = 'white')
invalid_page_l1.pack(expand = True)

main()
win.mainloop()
