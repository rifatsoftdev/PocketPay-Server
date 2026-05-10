import requests
import json

# API URL
URL = "http://192.168.1.100:8000/"

headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}


def get_request(url, headers=headers):
    response = requests.get(url, headers=headers)
    print(response)



# Test root endpoint
response = get_request(URL)