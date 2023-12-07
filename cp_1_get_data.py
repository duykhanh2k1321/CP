import os
import csv
import shutil
import requests
import subprocess
from time import sleep

url = 'https://wxnnlsrf-4000.asse.devtunnels.ms/api/hardware/get-all-rfid-data'
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2NGNmYmE4MGFhN2YwMjY0ZTY3ZTllN2UiLCJpYXQiOjE2OTc4OTc5ODgsImV4cCI6MzM5NTgzMTg0Nn0.51pWAZJKYH4qhJZpXLoa50VSdg09CUkA9YAic1USmZk'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

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

def get_data():
    if ping('google.com'):
        try:
            response = requests.get(url, headers = headers)
            if response.status_code == 200:
                data = response.json().get('userIdAndRFID', [])
                if data:
                    if not os.path.exists('rfid'):
                        os.makedirs('rfid')
                    existing_rfid_data = set()
                    existing_user_id = set()
                    with open('id.csv', 'w', newline = '') as id_file:
                        id_writer = csv.writer(id_file)
                        for item in data:
                            user_id = item.get('user_id', '')
                            rfid_data = item.get('rfid_data', '')
                            id_writer.writerow([user_id, rfid_data])
                            existing_rfid_data.add(rfid_data)
                            existing_user_id.add(user_id)
                            if not os.path.exists(f'rfid/{rfid_data}.csv'):
                                open(f'rfid/{rfid_data}.csv', 'w').close()
                    files_in_rfid_folder = os.listdir('rfid')
                    for file in files_in_rfid_folder:
                        file_name = os.path.splitext(file)[0]
                        if file_name not in existing_rfid_data:
                            os.remove(f'rfid/{file}')
                    files_in_fs_folder = os.listdir('fs')
                    for file in files_in_fs_folder:
                        file_name = os.path.splitext(file)[0]
                        if file_name not in existing_user_id:
                            os.remove(f'fs/{file}')
                    folder_in_fp_folder = os.listdir('fp')
                    for folder in folder_in_fp_folder:
                        folder_name = os.path.splitext(folder)[0]
                        if folder_name not in existing_user_id:
                            shutil.rmtree(f'fp/{folder}')
                    files_in_fd_folder = os.listdir('fd')
                    for file in files_in_fd_folder:
                        file_name = os.path.splitext(file)[0]
                        if file_name not in existing_user_id:
                            os.remove(f'fd/{file}')
                    print('Data has been written to id.csv and corresponding files created/deleted')
                else:
                    print('No data received from API')
            else:
                print('Request failed with status code:', response.status_code)
        except requests.Timeout:
            print('Request timeout\n')
        except requests.RequestException as e:
            print(f'Request error: {str(e)}\n')
                  
while True:
    get_data()
    sleep(300)
