import csv
import requests

from time import sleep

''' api_url '''
url = 'https://fc08-113-162-160-229.ngrok-free.app/api/hardware/get-all-rfid-data'

''' token '''
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2NGNmYmE4MGFhN2YwMjY0ZTY3ZTllN2UiLCJpYXQiOjE2OTc4OTc5ODgsImV4cCI6MzM5NTgzMTg0Nn0.51pWAZJKYH4qhJZpXLoa50VSdg09CUkA9YAic1USmZk'

''' headers '''
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

def get_data():
    try:
        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            data = response.json()
            rfid_list = [item['rfid_data'] for item in data.get('rfidData', [])]
            print('Success\n')
            with open('rfid_storage.csv', 'w', newline='') as rfid_file:
                rfid_writer = csv.writer(rfid_file)
                for rfid in rfid_list:
                    rfid_writer.writerow([rfid])
            print('Data has been written to rfid_storage.csv')
        else:
            print('Request failed with status code: \n', response.status_code)
    except requests.exceptions.RequestException as e:
            print(f'Error: {e}\n')
            
while True:
    get_data()
    sleep(300)
