import requests

def call_prediction_endpoint(data):
    url = "https://www.collegebasketball-ai.com/predictList"
    response = requests.post(url, json=data)
    return response.json()