import requests

def call_prediction_endpoint(data):
    url = "http://cbb-ai.eba-ets5efdu.us-east-2.elasticbeanstalk.com/predictList"
    response = requests.post(url, json=data)
    return response.json()