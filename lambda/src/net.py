import requests
from bs4 import BeautifulSoup
import boto3
import json
from decimal import Decimal
import os
from aws_lambda_powertools import Logger

logger = Logger(service="cbb-ai")


def read_file_from_s3(bucket, key):
    logger.info("Reading kenpom id file from s3")
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read()
    data = json.loads(data)
    return data

def net_rankings_to_dict(my_dict, flag):
    try:
        logger.info("Calling net rankings website")
        url = 'https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings'
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')
    except Exception as e:
        logger.error("Unable to get net rankings", error = str(e))
        return {}
    
    try:
        logger.info("Extracting data from net rankings")
        # Extract column headers from first row
        headers = [header.text.strip() for header in rows[0].find_all('th')]

        # Extract data from remaining rows
        data = []
        for row in rows[1:]:
            values = [value.text.strip() for value in row.find_all('td')]
            data.append(dict(zip(headers, values)))
    except Exception as e:
        logger.error("Unable to extract data from net rankings", error = str(e))
        return {}
    
    netRank = {}
    for team in data:
        try:
            if flag:
                netRank[my_dict[team['School']]] = int(team['Rank'])
            else:
                netRank[my_dict[team['School']]]  = None
        except:
            logger.error(f"Unable to find id for team net", team = team['School'])
    return netRank

# Update dynamoDB table with kenpom data
def update_dynamoDB_table(teamsData):
    try:
        logger.info("Updating dynamoDB table with net data")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('cbb-ai')
        for key, value in teamsData.items():
            table.update_item(
                Key={
                    'id': str(key)
                },
                UpdateExpression='SET ranks.net_rank = :val',
                ExpressionAttributeValues={
                    ':val': value
                }
            )
        logger.info("DynamoDB table updated with net data")
    except Exception as e:
        logger.error(f"Error updating dynamoDB table: {e}")

def lambda_handler(event, context):
    bucket = 'cbb-ai'
    key = 'net_id.json'
    flag = True if os.environ['NET_FLAG'] == "True" else False
    my_dict = read_file_from_s3(bucket, key)
    netRank = net_rankings_to_dict(my_dict, flag)
    update_dynamoDB_table(netRank)
    return {
        'statusCode': 200,
        'body': "data updated"
    }
