import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal


def boto3_setup():
    try:
        boto3.setup_default_session(aws_access_key_id=constants.aws_access_key_id, aws_secret_access_key=constants.aws_secret_access) 
    except:
        try:
            boto3.setup_default_session(profile_name='tarik0219')
        except:
            pass


def get_all_team_data():
    boto3_setup()
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('cbb-ai')
    response = table.scan()
    data = response['Items']
    return data

def convert_decimal_to_int(data):
    if isinstance(data, list):
        return [convert_decimal_to_int(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_decimal_to_int(value) for key, value in data.items()}
    elif isinstance(data, Decimal):
        return int(data)
    else:
        return data
    
import requests

def call_tournamentList_endpoint(data):
    url = "https://www.collegebasketball-ai.com/tournamentList"
    response = requests.post(url, json=data)
    return response.json()

teams = get_all_team_data()
teams = convert_decimal_to_int(teams)

teamData = {
    "teams": []
}
for team in teams:
    #chage from Decimal to int
    try:
        wins = team['records']['win']
        losses = team['records']['loss']
        q1w = team['projectedQuadRecords']['quad1']['wins']
        q1l = team['projectedQuadRecords']['quad1']['losses']
        q2w = team['projectedQuadRecords']['quad2']['wins']
        q2l = team['projectedQuadRecords']['quad2']['losses']
        q3w = team['projectedQuadRecords']['quad3']['wins']
        q3l = team['projectedQuadRecords']['quad3']['losses']
        q4w = team['projectedQuadRecords']['quad4']['wins']
        q4l = team['projectedQuadRecords']['quad4']['losses']
        rank = team['ranks']['rank']
        data = {
            "win": wins,
            "loss": losses,
            "q1w": q1w,
            "q1l": q1l,
            "q2w": q2w,
            "q2l": q2l,
            "q3w": q3w,
            "q3l": q3l,
            "q4w": q4w,
            "q4l": q4l,
            "rank": rank
        }
    except:
        print(team['teamName'])
    teamData['teams'].append(data)

response = call_tournamentList_endpoint(teamData)
#print(response)