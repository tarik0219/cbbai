import requests
from bs4 import BeautifulSoup
import boto3
import json
from aws_lambda_powertools import Logger

logger = Logger(service="cbb-ai")


def read_file_from_s3(bucket, key):
    logger.info("Reading kenpom id file from s3")
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read()
    data = json.loads(data)
    return data

def net_rankings_to_dict(my_dict):
    url = 'https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find('table')
    rows = table.find_all('tr')
    
    # Extract column headers from first row
    headers = [header.text.strip() for header in rows[0].find_all('th')]

    # Extract data from remaining rows
    data = []
    for row in rows[1:]:
        values = [value.text.strip() for value in row.find_all('td')]
        data.append(dict(zip(headers, values)))
    
    netRank = {}
    for team in data:
        try:
            netRank[my_dict[team['School']]] = int(team['Rank'])
        except:
            logger.error(f"Unable to find id for team net", team = team['School'])
    return netRank

