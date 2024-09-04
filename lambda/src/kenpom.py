from bs4 import BeautifulSoup
import requests
import re
import boto3
import json
from decimal import Decimal
from aws_lambda_powertools import Logger

logger = Logger(service="cbb-ai")


def team_name(team):
    team  = re.sub(r'\d+', '', team)
    team = team.rstrip()
    return team

def getKenpomWeb():
    try:
        url = "https://kenpom.com"
        page = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Safari/537.36'})
        data = page.text
        soup = BeautifulSoup(data, "html.parser")
        table = soup.find('table', id="ratings-table")
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
    except Exception as e:
        logger.error(f"Error getting kenpom data: {e}")
        rows = []
    return rows

def GetKenpomData(kp_id):
    logger.info("Getting kenpom data")
    rows = getKenpomWeb()
    logger.info("Parsing kenpom data")
    kenpom = []
    for row in rows:
        try:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            if len(cols) == 0:
                pass
            else:
                kenpomRank = int(cols[0])
                kenpomTeamName = team_name(cols[1])
                kenpomConf = cols[2]
                kenpomOff = float(cols[5])
                kenpomDef = float(cols[7])
                kenpomTempo = float(cols[9])
                send = {
                    "name" : kenpomTeamName,
                    "rank": kenpomRank,
                    "conference" : kenpomConf,
                    "offRating" : kenpomOff,
                    "defRating" : kenpomDef,
                    "TempoRating" : kenpomTempo,
                }
                teamId = kp_id[kenpomTeamName]
                send['id'] = teamId
                kenpom.append(send)
        except Exception as e:
            logger.error(f"Unable to find id for team kenpom", team = kenpomTeamName)
            pass
    return kenpom

def read_file_from_s3(bucket, key):
    logger.info("Reading kenpom id file from s3")
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read()
    return data


#Add or replace the kenpom attribute in the dynamoDB table by the id of the team
def update_dynamoDB_table(teamsData, conf_kp):
    try:
        logger.info("Updating dynamoDB table with kenpom data")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('cbb-ai')
        for teamData in teamsData:
            item = json.loads(json.dumps(teamData), parse_float=Decimal)
            table.update_item(
                Key={
                    'id': str(teamData['id'])
                },
                UpdateExpression='SET kenpom = :val',
                ExpressionAttributeValues={
                    ':val': item
                }
            )
            table.update_item(
                Key={
                    'id': str(teamData['id'])
                },
                UpdateExpression='SET conference = :val',
                ExpressionAttributeValues={
                    ':val': conf_kp[item['conference']]
                }
            )
        logger.info("DynamoDB table updated with kenpom data")
    except Exception as e:
        logger.error(f"Error updating dynamoDB table: {e}")

def lambda_handler(event, context):
    bucket = 'cbb-ai'
    key = 'id_kp.json'
    
    id_kp = read_file_from_s3(bucket, key)
    id_kp = json.loads(id_kp)
    kp_id = {v: k for k, v in id_kp.items()}

    key = "conf_kp_sportsreference.json"
    conf_kp = read_file_from_s3(bucket, key)
    conf_kp = json.loads(conf_kp)
    
    data = GetKenpomData(kp_id)
    update_dynamoDB_table(data,conf_kp)
    return {
        'statusCode': 200,
        'body': "data updated"
    }