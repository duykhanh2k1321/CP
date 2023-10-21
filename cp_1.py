import csv
import time
import requests

''' api_url '''
url = 'https://a888-113-172-235-185.ngrok-free.app/api/hardware/check-for-l1'

''' csv file '''
csv_file = 'rfid_storage.csv'

''' Read data from rfid_storage.csv '''
def read_rfid_data(csv_file):
    data_list = []
    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                rfid_input, rfid_time = row
                if rfid_time and rfid_time.strip():
                    data_list.append({'rfid_data': rfid_input, 'access_time': rfid_time})
    except (FileNotFoundError, StopIteration):
        pass
    return data_list

''' Send data to API '''
def rfid_data_to_api(url, data_list):
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

''' Send data to API when online '''
def send_rfid_data():
    data_list = read_rfid_data(csv_file)
    if data_list:
        if rfid_data_to_api(url, data_list):
            with open(csv_file, 'w', newline='') as file:
                writer = csv.writer(file)
                for data in data_list:
                    writer.writerow([data['rfid_input'], ''])
                print('Time data has been cleared after successful sending')
    else:
        print('No data to send to the API.')
    time.sleep(0.2)

while True:
    try:
        send_rfid_data()
    except requests.exceptions.ConnectionError:
        print('No connection. Waiting...\n')
    time.sleep(300)
