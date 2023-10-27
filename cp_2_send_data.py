import os
import csv
import json
import time
import requests
import schedule

''' api_url '''
url = 'https://a888-113-172-235-185.ngrok-free.app/api/hardware/check-for-l1'

''' Read data '''
def read_data():
    data_list = []
    with open('rfid_storage.csv', 'r') as rfid_file:
        rfid_reader = csv.reader(rfid_file)
        for rfid_row in rfid_reader:
            rfid = rfid_row[0]
            print(f'rfid: {rfid}')
            if os.path.exists(f'{rfid}.csv'):
                with open(f'{rfid}.csv', 'r') as time_file:
                    time_reader = csv.reader(time_file)
                    in_time = ''
                    out_time = ''
                    for i, time_row in enumerate(time_reader):
                        time = time_row[0]
                        if i == 0:
                            in_time = time
                        out_time = time
                        if i < 1:
                            out_time = ''
                    if in_time or out_time:
                        data_list.append({'rfid_data': rfid, 'clock_in_timestamp': in_time, 'clock_out_timestamp': out_time})
        print('')
        return data_list

''' Data to API '''
def data_to_api(url, data_list):
    try:
        response = requests.post(url, json = data_list)
        if response.status_code == 200:
            print('Success to send data to API\n')
            return True
        else:
            print('Fail to send data to API. Code: \n', response.status_code)
            return False
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}\n')
        return False
    
''' Clear data '''
def clear_data(data_list):
    for data in data_list:
        rfid = data['rfid_data']
        if os.path.exists(f'{rfid}.csv'):
            with open(f'{rfid}.csv', 'w') as time_file:
                time_file.truncate(0)
''' Send data '''
def send_data():
    data_list = read_data()
    if data_list:
        if data_to_api(url, data_list):
            clear_data(data_list)
            print('Time data has been cleared after successful sending')
            stop_sending()
        else:
            print('Failed to send data. Will retry in 30 seconds.')
            time.sleep(30)
            
def stop_sending():
    print('Stopping sending data')
    exit()
            
def main():
    schedule.every().day.at("21:30").do(send_data)
    schedule.every().day.at("22:00").do(stop_sending)
    while True:
        schedule.run_pending()

if __name__ == '__main__':
    main()
