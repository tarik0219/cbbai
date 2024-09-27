import requests
import boto3
import os

year = os.environ['YEAR']

def get_all_team_data():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('cbb-ai')
    response = table.scan()
    data = response['Items']
    return data

def call_espn_team_standings_api(year):
    url = f"http://site.api.espn.com/apis/v2/sports/basketball/mens-college-basketball/standings?season={year}"
    response = requests.request("GET", url).json()
    teams = {}
    for conference in response['children']:
        teamsData = conference['standings']['entries']
        for team in teamsData:
            try:
                teams[team['team']['id']] ={
                    "gamesBehind": team['stats'][67]['value'],
                    "conferenceStanding": int(team['stats'][5]['value']),
                    "win": int(team['stats'][12]['displayValue'].split("-")[0]),
                    "loss": int(team['stats'][12]['displayValue'].split("-")[1]),
                    "confWin": int(team['stats'][77]['displayValue'].split("-")[0]),
                    "confLoss": int(team['stats'][77]['displayValue'].split("-")[1])
                }
            except:
                pass
    return teams



def lambda_handler(event, context):
    pass