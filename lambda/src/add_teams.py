import boto3
import requests
import json

def boto3_setup():
    boto3.setup_default_session(profile_name='tarik0219')



boto3_setup()
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('cbb-ai')



url = "http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?limit=500"

headers = {
  'Content-Type': 'application/json'
}

response = requests.request("GET", url, headers=headers)

data = response.json()

for team in data['sports'][0]['leagues'][0]['teams']:
    teamName = team['team']['displayName']
    teamID = team['team']['id']
    teamData = {
        "teamName": teamName,
        "id": teamID
    }
    table.put_item(Item=teamData)
    print(f"Added team {teamName} with ID {teamID}")