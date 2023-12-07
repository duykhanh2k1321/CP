import os
import csv
import json
import time
import requests
import datetime
import subprocess

''' api_url '''
url = 'https://wxnnlsrf-4000.asse.devtunnels.ms/api/hardware/check-for-l1-backup'

''' Read data '''
def read_data():
    data_list = []
    with open('id.csv', 'r') as id_file:
        id_reader = csv.reader(id_file)
        for row in id_reader:
            _, rfid = row
            if rfid:
                print(f'rfid: {rfid}')
                if os.path.exists(f'rfid/{rfid}.csv'):
                    with open(f'rfid/{rfid}.csv', 'r') as time_file:
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

''' Data to API '''
def data_to_api(url, data_list):
    if ping('google.com'):
        try:
            response = requests.post(url, json = data_list)
            if response.status_code == 200:
                print('Update done')
                print('Success to send data to API\n')
                return True
            else:
                print('Fail to send data to API. Code: \n', response.status_code)
                return False
        except requests.Timeout:
            print('Request timeout\n')
            return False
        except requests.RequestException as e:
            print(f'Request error: {str(e)}\n')
            return False
    else:
        print('No Internet connection\n')
        return False
    
''' Clear data '''
def clear_data(data_list):
    for data in data_list:
        rfid = data['rfid_data']
        if os.path.exists(f'rfid/{rfid}.csv'):
            with open(f'rfid/{rfid}.csv', 'w') as time_file:
                time_file.truncate(0)
                
''' Send data '''    
def send_data():
    data_list = read_data()
    if data_list:
        if data_to_api(url, data_list):
            clear_data(data_list)
            print('Time data has been cleared after successful sending\n')
            exit()
        else:
            time.sleep(30)
    else:
        print('No data to send\n')
        exit()

def main():
    current_time = datetime.datetime.now().time()
    start_time = datetime.time(21, 30)
    end_time = datetime.time(22, 00)
    if start_time <= current_time <= end_time:
        send_data()

if __name__ == "__main__":
    main()
