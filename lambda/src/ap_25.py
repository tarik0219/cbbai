import requests
import boto3
from aws_lambda_powertools import Logger

logger = Logger(service="cbb-ai")

def addApRank(data):
    try:
        logger.info("Getting ap data")
        url = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/rankings"
        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)

        ranks = response.json()['rankings'][0]['ranks']
        others = response.json()['rankings'][0]['others']

        ap_ranks = {}
        for count,team in enumerate(ranks):
            ap_ranks[team['team']['id']] = count + 1
            
        for count,team in enumerate(others):
            ap_ranks[team['team']['id']] = count + 26

        length_rank = len(ap_ranks)
        for count,team in enumerate(data):
            if team['id'] in ap_ranks:
                if "ranks" not in team:
                    team['ranks'] = {}
                team['ranks']['ap_rank'] = ap_ranks[team['id']]
            else:
                if "ranks" not in team:
                    team['ranks'] = {}
                team['ranks']['ap_rank'] = None
            data[count] = team
    except Exception as e:
        logger.error(f"Error getting ap data: {e}")
        data = []
    return data

def update_dynamoDB_table(data):
    logger.info("Updating dynamoDB table")
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('cbb-ai')
        for team in data:
            table.update_item(
                Key={
                    'id': team['id']
                },
                UpdateExpression="set ranks = :r",
                ExpressionAttributeValues={
                    ':r': team['ranks']
                },
                ReturnValues="UPDATED_NEW"
            )
        logger.info("DynamoDB table updated")
    except Exception as e:
        logger.error(f"Error updating dynamoDB table: {e}")


def lambda_handler(event, context):
    logger.info("Getting data from dynamoDB")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('cbb-ai')
    data = table.scan()['Items']
    data = addApRank(data)
    update_dynamoDB_table(data)
    return {
        'statusCode': 200,
        'body': "data updated"
    }