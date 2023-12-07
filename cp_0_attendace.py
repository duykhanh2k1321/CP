import os
import csv
import cv2
import json
import time
import requests
import subprocess
import numpy as np
import tkinter as tk
import RPi.GPIO as GPIO
import tflite_runtime.interpreter as tflite

from time import sleep
from time import strftime
from mfrc522 import SimpleMFRC522
from time import time as get_current_time

''' api_url '''
url1 = 'https://wxnnlsrf-4000.asse.devtunnels.ms/api/hardware/check-for-l1'
url2 = 'https://wxnnlsrf-4000.asse.devtunnels.ms/api/hardware/check-for-l2'

''' Define variables '''
rfid_input = None
pin_input = None
user_id = None
reader = None
result = None
access = None

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
    
''' Valid RFID/PIN/FACE '''
def valid_data():
    reset_outputs()
    beep1()
    reset_outputs()
    
''' Invalid RFID/PIN/FACE '''
def invalid_data():
    reset_outputs()
    beep2()
    reset_outputs()
    
''' Error '''
def error():
    print('Error')
    reset_outputs()
    beep2()
    reset_outputs()
    
''' Unlock and lock after 3 seconds '''
def control_lock():
    print('Unlocking')
    print('After 3 seconds')
    GPIO.output(th3, 0)
    GPIO.output(th4, 1)
    sleep(3)
    print('Locking\n')
    GPIO.output(th3, 1)
    GPIO.output(th4, 0)
    reset_outputs()
    access_granted_page.pack_forget()
    main()
    
''' Ping to Google for checking Internet connection '''   
def ping(host):
    try:
        subprocess.run(['ping', '-c', '1', host], check = True, timeout = 1)
        print('')
        return True
    except subprocess.CalledProcessError:
        print('No Internet connection\n')
        return False
    except subprocess.TimeoutExpired:
        print('No Internet connection\n')
        return False
    
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
        button.config(state = 'disabled')
    check.config(state = 'disabled')
    delete.config(state = 'disabled')
    back.config(state = 'disabled')

def enable_buttons():
    for button in keypad.winfo_children():
        button.config(state = 'normal')
    check.config(state = 'normal')
    delete.config(state = 'normal')
    back.config(state = 'normal')
   
def time():
    string = strftime('%A - %d/%m/%Y - %X')
    main_page_l0.config(text = string)
    rfid_page_l0.config(text = string)
    pin_page_l0.config(text = string)
    face_add_page_l0.config(text = string)
    face_scan_page_l0.config(text = string)
    win.after(1000, time)

''' Check input data '''
''' Check RFID '''
def rfid_read():
    global rfid_input, user_id
    rfid_input, _ = reader.read()
    print(f'RFID: {rfid_input}')
    print('Do not scan RFID card/tag')
    print('Connecting to REST API Server')
    print('Checking RFID\n')
    rfid_error, rfid_recieve = rfid_check(rfid_input)
    if rfid_error:
        print('No connection to API')
        if os.path.exists(f'rfid/{rfid_input}.csv'):
            print(f'Valid rfid: {rfid_input}')
            with open('id.csv', mode = 'r') as file:
                id_reader = csv.reader(file)
                for row in id_reader:
                    if row[1] == str(rfid_input):
                        user_id = row[0]
                        print(f'USER ID: {user_id}')
            print('Pass level 1 security')
            print('LEVEL 1 VALID page\n')
            rfid_input_page.pack_forget()
            level1_valid_page.pack(expand = True, fill = 'both')
            win.after(1000, valid_data)
            win.after(2000, face_scan)
        else:
            print(f'Invalid rfid: {rfid_input}')
            print('Not pass level 1 security')
            print('LEVEL 1 INVALID page\n')
            rfid_input_page.pack_forget()
            level1_invalid_page.pack(expand = True, fill = 'both')
            win.after(1000, invalid_data)
            win.after(2000, level1_to_main)
    elif rfid_recieve:
        print(f'Info:\n{rfid_recieve.text}')
        user_id = json.loads(rfid_recieve.text).get('user_id', None)
        print(f'Valid rfid: {rfid_input}')
        print(f'USER ID: {user_id}')
        print('Pass level 1 security')
        print('LEVEL 1 VALID page\n')
        rfid_input_page.pack_forget()
        level1_valid_page.pack(expand = True, fill = 'both')
        win.after(1000, valid_data)
        win.after(2000, face_scan)
    else:       
        print(f'Info:\n{rfid_recieve.text}\n')
        print(f'Invalid rfid: {rfid_input}')
        print('Not pass level 1 security')
        print('LEVEL 1 INVALID page\n')
        rfid_input_page.pack_forget()
        level1_invalid_page.pack(expand = True, fill = 'both')
        win.after(1000, invalid_data)
        win.after(2000, level1_to_main)

def rfid_check(rfid_input):
    rfid_error = False
    if ping('google.com'):
        try:
            rfid_recieve = requests.post(url1, json = {'rfid_data': rfid_input}, timeout = 1)
            print(f'{rfid_recieve}\n')
            return rfid_error, rfid_recieve
        except requests.Timeout:
            print('Request timeout\n')
            rfid_error = True
            return rfid_error, False
        except requests.RequestException as e:
            print(f'Request error: {str(e)}\n')
            rfid_error = True
            return rfid_error, False
    else:
        rfid_error = True
        return rfid_error, False
    
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
        error_page.pack(expand = True, fill = 'both')
        win.after(1000, error)
        win.after(2000, error_to_main)
    elif pin_recieve:
        pin_input = ''
        pin_input_var.set('')
        print(f'Info:\n{pin_recieve.text}\n')
        print('VALID page\n')
        pin_input_page.pack_forget()
        enable_buttons()
        valid_page_c1.pack(expand = True, fill = 'both')
        win.after(1000, valid_data)
        win.after(2000, scan_face)
    else:
        pin_input = ''
        pin_input_var.set('')
        print(f'Info:\n{pin_recieve.text}\n')
        print('INVALID page\n')
        pin_input_page.pack_forget()
        enable_buttons()
        invalid_page_c1.pack(expand = True, fill = 'both')
        win.after(1000, invalid_data)
        win.after(2000, level1_to_main)

def pin_check(pin_input):
    pin_error = False
    if ping('google.com'):
        try:
            pin_recieve = requests.post(url1, json = {'pin_code': pin_input}, timeout = 1)
            print(f'{pin_recieve}\n')
            return pin_error, pin_recieve
        except requests.Timeout:
            print('Request timeout\n')
            pin_error = True
            return pin_error, False
        except requests.RequestException as e:
            print(f'Request error: {str(e)}\n')
            pin_error = True
            return pin_error, False
    else:
        pin_error = True
        return pin_error, False
    
''' Check face '''
def face_scan_read():
    global user_id
    face_scan_page_l2.configure(state = 'disabled')
    face_scan_page_l3.configure(state = 'disabled')
    # Load the TFLite model
    interpreter = tflite.Interpreter(model_path = 'model.tflite')
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')  # Load the pre-trained face detection model
    os.makedirs('fs', exist_ok = True)  # Directory to save feature vectors
    cap = cv2.VideoCapture(0)  # Access the USB webcam
    cv2.namedWindow('Capture Interface')  # Create a window to display interface
    start_time = get_current_time()
    while (get_current_time() - start_time) < 5:
        ret, frame = cap.read()
        countdown_text = 'Capture starts in: ' + str(5 - int(get_current_time() - start_time)) + ' seconds'
        cv2.putText(frame, countdown_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('Capture Interface', frame)
        cv2.waitKey(1)
    # Process the webcam frames
    vector = []  # Initialize vector to store the single facial feature
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow('Capture Interface', frame)  # Display camera feed
        cv2.waitKey(1)  # Allow OpenCV to refresh the window
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert the frame to grayscale
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor = 1.3, minNeighbors = 6, minSize = (120, 120))  # Detect faces in the grayscale frame
        # Process detected face in the frame
        for (x, y, w, h) in faces:
            expand_roi_y = int(0.2 * h)
            face_roi = frame[max(0, y - expand_roi_y):min(frame.shape[0], y + h + expand_roi_y), x:x + w]
            cv2.imwrite(f'fs/{user_id}.jpg', face_roi)
            input_image_resized = cv2.resize(face_roi, (input_details[0]['shape'][2], input_details[0]['shape'][1]))
            input_image_resized = np.expand_dims(input_image_resized, axis=0)
            input_image_resized = input_image_resized.astype(np.float32)
            interpreter.set_tensor(input_details[0]['index'], input_image_resized)  # Set input tensor for the model
            interpreter.invoke()  # Run inference
            output_data = interpreter.get_tensor(output_details[0]['index'])  # Get output tensor
            vector = output_data.flatten()  # Store the extracted facial features as the single vector
            break  # Break after processing the first detected face
        if vector is not None:  # If a vector has been extracted, break the loop
            break
    cap.release()
    cv2.destroyAllWindows()
    # Save the extracted facial feature to a CSV file
    output_file = os.path.join('fs', f'{user_id}.csv')
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(vector.tolist())
    print('Face scan read, done\n')
    face_check()
    
def face_check():
    global rfid_input, user_id, result
    print(f'RFID: {rfid_input}\nUSER ID: {user_id}\n')
    with open(f'fs/{user_id}.csv', mode='r') as file:
        reader = csv.reader(file)
        fs_features = [np.array(row, dtype = np.float32) for row in reader]
    with open(f'fd/{user_id}.csv', mode = 'r') as file:
        reader = csv.reader(file)
        fd_features = [np.array(row, dtype = np.float32) for row in reader]
    max_similarity = -1
    min_similarity = float('inf')
    total_similarity = 0
    num_comparisons = 0
    similarity_above_80_count = 0
    for i, fs_vector in enumerate(fs_features):
        for j, fd_vector in enumerate(fd_features):
            similarity = np.dot(fs_vector, fd_vector) / (np.linalg.norm(fs_vector) * np.linalg.norm(fd_vector))
            max_similarity = max(max_similarity, similarity)
            min_similarity = min(min_similarity, similarity)
            total_similarity += similarity
            num_comparisons += 1
            print(f'Percentage between vector {i} in fs/{user_id}.csv and vector {j} in fd/{user_id}.csv : {similarity * 100}%')
            if similarity >= 0.8:
                similarity_above_80_count += 1
    print(f'Maximum similarity: {max_similarity * 100}%')
    print(f'Minimum similarity: {min_similarity * 100}%')
    similarity_above_80_percent = (similarity_above_80_count / num_comparisons) * 100
    print(f'Percentage of ratios greater than or equal to 80%: {similarity_above_80_percent}%\n')
    face_scan_page.pack_forget()
    if similarity_above_80_percent >= 80:
        user_time = int(get_current_time())
        print('Valid face')
        print(f'USER ID: {user_id}')
        print(f'USER TIME: {user_time}\n')
        print('Pass level 2 security\n')
        print('LEVEL 2 VALID page\n')
        level2_valid_page.pack(expand = True, fill = 'both')
        win.after(1000, valid_data)
        win.after(2000, access_handling)
    else:
        print('Invalid face')
        print('Not pass level 2 security\n')
        print('LEVEL 2 INVALID page\n')
        level2_invalid_page.pack(expand = True, fill = 'both')
        win.after(1000, invalid_data)
        win.after(2000, level2_to_main)
        
def access_handling():
    global rfid_input, user_id
    result = ({'user_id': user_id, 'access_status': 'true'})
    print('Access handling')
    print('Connecting to REST API Server\n')
    access_error = access_check(result)
    if access_error:
        access_time = int(get_current_time())
        print('No connection to API\n')
        if os.path.exists(f'rfid/{rfid_input}.csv'):
            with open(f'rfid/{rfid_input}.csv', 'a', newline = '') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow([access_time])
            print(f'RFID: {rfid_input}')
            print(f'USER ID: {user_id}')
            print(f'Access granted')
            print('ACCESS GRANTED page\n')
            level2_valid_page.pack_forget()
            access_granted_page.pack(expand = True, fill = 'both')
            win.after(1000, valid_data)
            win.after(2000, control_lock)
        else:
            print(f'RFID: {rfid_input}')
            print(f'USER ID: {user_id}')
            print(f'Access denied')
            print('ACCESS DENIED page\n')
            level2_valid_page.pack_forget()
            access_denied_page.pack(expand = True, fill = 'both')
            win.after(1000, invalid_data)
            win.after(2000, access_check_to_main)
    else:
        print(f'Info:\n{access_receive.text}\n')
        print(f'RFID: {rfid_input}')
        print(f'USER ID: {user_id}')
        print(f'Access granted')
        print('ACCESS GRANTED page\n')
        level2_valid_page.pack_forget()
        access_granted_page.pack(expand = True, fill = 'both')
        win.after(1000, valid_data)
        win.after(2000, control_lock)

def access_check(result):
    access_error = False
    if ping('google.com'):
        try:
            access_receive = requests.post(url2, json = result, timeout = 1)
            print(f'{api_check_response}\n')
            return access_error
        except requests.Timeout:
            print('Request timeout\n')
            access_error = True
            return access_error
        except requests.RequestException as e:
            print(f'Request error: {str(e)}\n')
            access_error = True
            return access_error
    else:
        access_error = True
        return access_error
        
''' Check FACE ADD RFID '''
def face_add_rfid_read():
    global rfid_input
    rfid_input, _ = reader.read()
    print(f'RFID: {rfid_input}')
    print('Do not scan RFID card/tag')
    print('Connecting to REST API Server')
    print('Checking RFID\n')
    sleep (1)
    rfid_error, rfid_recieve = face_add_rfid_check(rfid_input)
    if rfid_error:
        print('NO CONNECTION TO API\n')
        if os.path.exists(f'rfid/{rfid_input}.csv'):
            print(f'Valid rfid: {rfid_input}')
            print('Pass face add security')
            print('FACE ADD VALID page\n')
            face_add_rfid_input_page.pack_forget()
            face_add_valid_page.pack(expand = True, fill = 'both')
            win.after(1000, valid_data)
            win.after(2000, face_add_add)
            win.after(3000, face_add_done)
        else:
            print(f'Invalid rfid: {rfid_input}')
            print('Not pass face add security')
            print('FACE ADD INVALID page\n')
            face_add_rfid_input_page.pack_forget()
            face_add_invalid_page.pack(expand = True, fill = 'both')
            win.after(1000, invalid_data)
            win.after(2000, face_add_invalid_to_main)
    elif rfid_recieve:
        print(f'Info:\n{rfid_recieve.text}\n')
        print(f'Valid rfid: {rfid_input}')
        print('Pass face add security')
        print('FACE ADD VALID page\n')
        face_add_rfid_input_page.pack_forget()
        face_add_valid_page.pack(expand = True, fill = 'both')
        win.after(1000, valid_data)
        win.after(2000, face_add_add)
        win.after(3000, face_add_done)
    else:       
        print(f'Info:\n{rfid_recieve.text}\n')
        print(f'Invalid rfid: {rfid_input}')
        print('Not pass face add security')
        print('FACE ADD INVALID page\n')
        face_add_rfid_input_page.pack_forget()
        face_add_invalid_page.pack(expand = True, fill = 'both')
        win.after(1000, invalid_data)
        win.after(2000, face_add_invalid_to_main)

def face_add_rfid_check(rfid_input):
    rfid_error = False
    if ping('google.com'):
        try:
            rfid_recieve = requests.post(url1, json = {'rfid_data': rfid_input}, timeout = 1)
            print(f'{rfid_recieve}\n')
            return rfid_error, rfid_recieve
        except requests.Timeout:
            print('Request timeout\n')
            rfid_error = True
            return rfid_error, False
        except requests.RequestException as e:
            print(f'Request error: {str(e)}\n')
            rfid_error = True
            return rfid_error, False
    else:
        rfid_error = True
        return rfid_error, False

''' Create face database '''
def face_add_add():
    global rfid_input, user_id
    print(f'RFID: {rfid_input}')
    with open('id.csv', mode = 'r') as file:
        id_reader = csv.reader(file)
        for row in id_reader:
            if row[1] == str(rfid_input):
                user_id = row[0]
                print(f'USER ID: {user_id}\n')
    # Load the TFLite model
    interpreter = tflite.Interpreter(model_path = 'model.tflite')
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml') # Load the pre-trained face detection model
    os.makedirs('fd', exist_ok = True) # Directory to save feature vectors
    os.makedirs(f'fp/{user_id}', exist_ok = True) # Directory to save cropped face images
    cap = cv2.VideoCapture(0) # Access the USB webcam
    vectors = []
    cv2.namedWindow('Capture Interface') # Create a window to display interface
    start_time = get_current_time()
    while (get_current_time() - start_time) < 5:
        ret, frame = cap.read()
        countdown_text = 'Capture starts in: ' + str(5 - int(get_current_time() - start_time)) + ' seconds'
        cv2.putText(frame, countdown_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('Capture Interface', frame)
        cv2.waitKey(1)
    # Process the webcam frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow('Capture Interface', frame) # Display camera feed
        cv2.waitKey(1)  # Allow OpenCV to refresh the window
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Convert the frame to grayscale        
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor = 1.3, minNeighbors = 6, minSize = (120, 120)) # Detect faces in the grayscale frame
        # Process detected face in the frame
        for (x, y, w, h) in faces:
            expand_roi_y = int(0.2 * h)
            face_roi = frame[max(0, y - expand_roi_y):min(frame.shape[0], y + h + expand_roi_y), x:x+w]
            face_img_path = os.path.join(f'fp/{user_id}', f'{len(vectors)}.jpg')
            cv2.imwrite(face_img_path, face_roi)
            input_image_resized = cv2.resize(face_roi, (input_details[0]['shape'][2], input_details[0]['shape'][1]))
            input_image_resized = np.expand_dims(input_image_resized, axis=0)
            input_image_resized = input_image_resized.astype(np.float32)
            interpreter.set_tensor(input_details[0]['index'], input_image_resized) # Set input tensor for the model
            interpreter.invoke() # Run inference
            output_data = interpreter.get_tensor(output_details[0]['index']) # Get output tensor
            vectors.append(output_data.flatten()) # Save the extracted facial features to the list
        if len(vectors) >= 60:
            break
    cap.release()
    cv2.destroyAllWindows()
    # Save all the extracted facial features to a CSV file along with image names
    output_file = os.path.join('fd', f'{user_id}.csv')
    with open(output_file, mode = 'w', newline = '') as file:
        writer = csv.writer(file)
        for vector in vectors:
            writer.writerow(vector.tolist())
    print('Face add add, done\n')

''' MAIN '''
def main():
    setup()
    time()
    print('Level 1 security\nMAIN page\n')
    main_page.pack(expand = True, fill = 'both')
    
''' RFID '''
def rfid():
    print('MAIN page to RFID page\nRFID page\n')
    main_page.pack_forget()
    rfid_page.pack(expand = True, fill = 'both')
    
''' RFID INPUT '''    
def rfid_input():
    print('RFID page to RFID INPUT page')
    print('RFID INPUT page\nPlease input RFID card/tag\n')
    rfid_page.pack_forget()
    rfid_input_page.pack(expand = True, fill = 'both')
    win.after(100, rfid_read)
    
''' RFID TO MAIN '''    
def rfid_to_main():
    print('RFID page to MAIN page\nMAIN page\n')
    rfid_page.pack_forget()
    main()

''' PIN '''
def pin():
    print('MAIN page to PIN page\nMAIN page\n')
    main_page.pack_forget()
    pin_page.pack(expand = True, fill = 'both')
    
''' PIN INPUT '''        
def pin_input():
    print('PIN page to PIN INPUT page')
    print('PIN INPUT page\nPlease input PIN\n')
    pin_page.pack_forget()
    pin_input_page.pack(expand = True, fill = 'both')

''' PIN TO MAIN '''
def pin_to_main():
    print('PIN page to MAIN page\nMAIN page\n')
    pin_page.pack_forget()
    main()

''' PIN INPUT TO MAIN'''
def pin_input_to_main():
    global pin_input
    pin_input = ''
    pin_input_var.set('')
    print(f'Clear input PIN')
    print(f'PIN INPUT page to MAIN page\nMAIN page\n')
    pin_input_page.pack_forget()
    main()
    
''' FACE ADD '''    
def face_add():
    print('MAIN page to FACE ADD page\nFACE ADD page\n')
    main_page.pack_forget()
    face_add_page.pack(expand = True, fill = 'both')
    
''' FACE ADD RFID INPUT '''    
def face_add_rfid_input():
    print('FACE ADD to FACE ADD RFID INPUT page')
    print('FACE ADD RFID INPUT page\nPlease input RFID card/tag\n')
    face_add_page.pack_forget()
    face_add_rfid_input_page.pack(expand = True, fill = 'both')
    win.after(100, face_add_rfid_read)
    
''' FACE ADD TO MAIN '''    
def face_add_to_main():
    print('FACE ADD page to MAIN page\nMAIN page\n')
    face_add_page.pack_forget()
    main()
    
''' FACE ADD DONE '''    
def face_add_done():
    print('FACE ADD VALID page to FACE ADD DONE page\nFACE ADD DONE page\n')
    face_add_valid_page.pack_forget()
    face_add_done_page.pack(expand = True, fill = 'both')
    win.after(1000, face_add_done_to_main)
    
''' FACE ADD DONE TO MAIN '''    
def face_add_done_to_main():
    print('FACE ADD DONE page to MAIN page\nMAIN page\n')
    face_add_done_page.pack_forget()
    main()
    
''' FACE ADD INVALID TO MAIN '''
def face_add_invalid_to_main():
    print('FACE ADD INVALID page to MAIN page\nMAIN page\n')
    face_add_invalid_page.pack_forget()
    main()
    
''' FACE SCAN ''' 
def face_scan():
    print('LEVEL 1 VALID DATA page to FACE SCAN page\nFACE SCAN page\n')
    level1_valid_page.pack_forget()
    face_scan_page_l2.configure(state = 'normal')
    face_scan_page_l3.configure(state = 'normal')
    face_scan_page.pack(expand = True, fill = 'both')
    
''' FACE SCAN TO MAIN ''' 
def face_scan_to_main():
    print('FACE SCAN page to MAIN page\nMAIN page\n')
    face_scan_page.pack_forget()
    main()
    
''' LEVEL 1 TO MAIN '''    
def level1_to_main():
    print('LEVEL 1 INVALID page to MAIN page\nMAIN page\n')
    level1_invalid_page.pack_forget()
    main()
    
''' LEVEL 2 TO MAIN '''    
def level2_to_main():
    print('LEVEL 2 INVALID page to MAIN page\nMAIN page\n')
    level2_invalid_page.pack_forget()
    main()
    
''' ACCESS CHECK TO MAIN '''    
def access_check_to_main():
    print('ACCESS CHECK page to MAIN page\nMAIN page\n')
    access_denied_page.pack_forget()
    main()

''' ERROR TO MAIN '''
def error_to_main():
    print('ERROR page to MAIN page\nMAIN page\n')
    error_page.pack_forget()
    main()

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

''' Choose mode RFID/PIN/FACE ADD - MAIN page '''
main_page = tk.Frame(win)
main_page_l0 = tk.Label(main_page, font = ('arial', 50))
main_page_l0.pack()
main_page_l1 = tk.Label(main_page, text = 'LEVEL 1 SECURITY\nMAIN', font = ('arial', 50))
main_page_l1.pack()
main_page_l2 = tk.Button(main_page, text = 'RFID', font = ('arial', 50), bg = 'green', fg = 'white', command = rfid)
main_page_l2.pack(padx = 350, expand = True, fill = 'x')
main_page_l3 = tk.Button(main_page, text = 'PIN', font = ('arial', 50), bg = 'green', fg = 'white', command = pin)
main_page_l3.pack(padx = 350, expand = True, fill = 'x')
main_page_l2 = tk.Button(main_page, text = 'FACE ADD', font = ('arial', 50), bg = 'green', fg = 'white', command = face_add)
main_page_l2.pack(padx = 350, expand = True, fill = 'x')

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

''' LEVEL 1 VALID DATA page '''
level1_valid_page = tk.Frame(win)
level1_valid_page_l0 = tk.Label(level1_valid_page, text = 'LEVEL 1 SECURITY\nVALID', font = ('arial', 50))
level1_valid_page_l0.pack()
level1_valid_page_l1 = tk.Label(level1_valid_page, text = 'VALID DATA\nPASS LEVEL 1 SECURITY', font = ('arial', 50), bg = 'green', fg = 'white')
level1_valid_page_l1.pack(expand = True)

''' LEVEL 1 INVALID DATA page '''
level1_invalid_page = tk.Frame(win)
level1_invalid_page_l0 = tk.Label(level1_invalid_page, text = 'LEVEL 1 SECURITY\nINVALID', font = ('arial', 50))
level1_invalid_page_l0.pack()
level1_invalid_page_l1 = tk.Label(level1_invalid_page, text = 'INVALID DATA\nBACK TO MAIN WINDOW', font = ('arial', 50), bg = 'red', fg = 'white')
level1_invalid_page_l1.pack(expand = True)

''' ERROR page '''
error_page = tk.Frame(win)
error_page_l0 = tk.Label(error_page, text = 'LEVEL 1 SECURITY\nERROR', font = ('arial', 50))
error_page_l0.pack()
error_page_l1 = tk.Label(error_page, text = 'NO CONNECTION TO API\nBACK TO MAIN WINDOW', font = ('arial', 50), bg = 'red', fg = 'white')
error_page_l1.pack(expand = True)

''' FACE ADD page '''
face_add_page = tk.Frame(win)
face_add_page_l0 = tk.Label(face_add_page, font = ('arial', 50))
face_add_page_l0.pack()
face_add_page_l1 = tk.Label(face_add_page, text = 'FACE ADD\nRFID', font = ('arial', 50))
face_add_page_l1.pack()
face_add_page_l2 = tk.Button(face_add_page, text = 'INPUT RFID', font = ('arial', 50), bg ='green', fg = 'white', command = face_add_rfid_input)
face_add_page_l2.pack(padx = 350, expand = True, fill = 'x')
face_add_page_l3 = tk.Button(face_add_page, text = 'BACK', font = ('arial', 50), bg = 'black', fg = 'white', command = face_add_to_main)
face_add_page_l3.pack(padx = 350, expand = True, fill = 'x')

''' FACE ADD RFID INPUT page '''
face_add_rfid_input_page = tk.Frame(win)
face_add_rfid_input_page_l0 = tk.Label(face_add_rfid_input_page, text = 'FACE ADD\nRFID INPUT', font = ('arial', 50))
face_add_rfid_input_page_l0.pack()
face_add_rfid_input_page_l1 = tk.Label(face_add_rfid_input_page, text = 'PLEASE INPUT RFID CARD/TAG', font = ('arial', 50), bg ='green', fg = 'white')
face_add_rfid_input_page_l1.pack(expand = True)

''' FACE ADD VALID DATA page '''
face_add_valid_page = tk.Frame(win)
face_add_valid_page_l0 = tk.Label(face_add_valid_page, text = 'FACE ADD\nVALID', font = ('arial', 50))
face_add_valid_page_l0.pack()
face_add_valid_page_l1 = tk.Label(face_add_valid_page, text = 'VALID RFID\nENABLE FACE SCANNING', font = ('arial', 50), bg ='green', fg = 'white')
face_add_valid_page_l1.pack(expand = True)

''' FACE ADD INVALID DATA page '''
face_add_invalid_page = tk.Frame(win)
face_add_invalid_page_l0 = tk.Label(face_add_invalid_page, text = 'FACE ADD\nINVALID', font = ('arial', 50))
face_add_invalid_page_l0.pack()
face_add_invalid_page_l1 = tk.Label(face_add_invalid_page, text = 'INVALID RFID\nBACK TO MAIN WINDOW', font = ('arial', 50), bg ='green', fg = 'white')
face_add_invalid_page_l1.pack(expand = True)

''' FACE ADD DONE page '''
face_add_done_page = tk.Frame(win)
face_add_done_page_l0 = tk.Label(face_add_done_page, text = 'FACE ADD\nDONE', font = ('arial', 50))
face_add_done_page_l0.pack()
face_add_done_page_l1 = tk.Label(face_add_done_page, text = 'FACE ADD SUCCEED\nBACK TO MAIN WINDOW', font = ('arial', 50), bg = 'green', fg = 'white')
face_add_done_page_l1.pack(expand = True)

''' FACE SCAN page '''
face_scan_page = tk.Frame(win)
face_scan_page_l0 = tk.Label(face_scan_page, font = ('arial', 50))
face_scan_page_l0.pack()
face_scan_page_l1 = tk.Label(face_scan_page, text = 'LEVEL 2 SECURITY\nFACE SCAN', font = ('arial', 50))
face_scan_page_l1.pack()
face_scan_page_l2 = tk.Button(face_scan_page, text = 'START', font = ('arial', 50), bg = 'green', fg = 'white', command = face_scan_read)
face_scan_page_l2.pack(padx = 350, expand = True, fill = 'x')
face_scan_page_l3 = tk.Button(face_scan_page, text = 'BACK', font = ('arial', 50), bg = 'black', fg = 'white', command = face_scan_to_main)
face_scan_page_l3.pack(padx = 350, expand = True, fill = 'x')

''' LEVEL 2 VALID DATA page '''
level2_valid_page = tk.Frame(win)
level2_valid_page_l0 = tk.Label(level2_valid_page, text = 'LEVEL 2 SECURITY\nVALID', font = ('arial', 50))
level2_valid_page_l0.pack()
level2_valid_page_l2 = tk.Label(level2_valid_page, text = 'VALID DATA\nPASS LEVEL 2 SECURITY', font = ('arial', 50), bg = 'green', fg = 'white')
level2_valid_page_l2.pack(expand = True)

''' LEVEL 2 INVALID DATA page '''
level2_invalid_page = tk.Frame(win)
level2_invalid_page_l0 = tk.Label(level2_invalid_page, text = 'LEVEL 2 SECURITY\nINVALID', font = ('arial', 50))
level2_invalid_page_l0.pack()
level2_invalid_page_l2 = tk.Label(level2_invalid_page, text = 'INVALID DATA\nBACK TO MAIN WINDOW', font = ('arial', 50), bg = 'red', fg = 'white')
level2_invalid_page_l2.pack(expand = True)

''' ACCESS GRANTED page '''
access_granted_page = tk.Frame(win)
access_granted_page_l0 = tk.Label(access_granted_page, text = 'ACCESS CHECK\nGRANTED', font = ('arial', 50))
access_granted_page_l0.pack()
access_granted_page_l2 = tk.Label(access_granted_page, text = 'ACCESS GRANTED\nUNLOCKING FOR 3 SECONDS', font = ('arial', 50), bg = 'green', fg = 'white')
access_granted_page_l2.pack(expand = True)

''' ACCESS DENIED page '''
access_denied_page = tk.Frame(win)
access_denied_page_l0 = tk.Label(access_denied_page, text = 'ACCESS CHECK\nDENIED', font = ('arial', 50))
access_denied_page_l0.pack()
access_denied_page_l2 = tk.Label(access_denied_page, text = 'ACCESS DENIED\nBACK TO MAIN WINDOW', font = ('arial', 50), bg = 'red', fg = 'white')
access_denied_page_l2.pack(expand = True)

main()
win.mainloop()
