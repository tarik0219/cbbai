import bs4 as bs
import urllib.request
import json
from decimal import Decimal
import boto3
from aws_lambda_powertools import Logger

logger = Logger(service="cbb-ai")

def get_url_bt(year):
    return "https://barttorvik.com/trank.php?year={}&sort=&conlimit=#".format(year)


def get_table_rows_bt(year):
    """
    Return Rows of data.
    """
    try:
        url = get_url_bt(year)
        source = urllib.request.urlopen(url).read()
        soup = bs.BeautifulSoup(source,"html.parser")
        table = soup.find('table')
        table_body = table.find('tbody')
        for br in soup.find_all("br"):
            br.replace_with("@")
        rows = table_body.find_all('tr')
        return rows
    except Exception as e:
        logger.error(f"Error getting barttorvik data: {e}")
        return []

def change_team_names_bt(x):
    length = len(x.split('@'))
    if length > 1:
        return x.split('@')[0]
    else:
        return x

def GetBarttorvikData(year,bt_id):
    logger.info("Getting barttorvik data")
    rows = get_table_rows_bt(year)
    logger.info("Parsing barttorvik data")
    barttorvik = []
    for row in rows:
        try:
            send = {}
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            send = {
                    "name" : change_team_names_bt(cols[1]),
                    "rank": int(change_team_names_bt(cols[0])),
                    "offRating" : float(change_team_names_bt(cols[5])),
                    "defRating" : float(change_team_names_bt(cols[6])),
                    "TempoRating" : float(change_team_names_bt(cols[22]))
                }
            try:
                teamId = bt_id[change_team_names_bt(cols[1])]
                send['id'] = teamId
                barttorvik.append(send)
            except Exception as e:
                logger.error(f"Error parsing barttorvik data: {e}", team = change_team_names_bt(cols[1]))
                pass
        except:
            pass       
    return barttorvik

def read_file_from_s3(bucket, key):
    logger.info("Reading bartorvik id file from s3")
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read()
    return data

#Add or replace the kenpom attribute in the dynamoDB table by the id of the team
def update_dynamoDB_table(teamsData):
    try:
        logger.info("Updating dynamoDB table with barttorvik data")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('cbb-ai')
        for teamData in teamsData:
            item = json.loads(json.dumps(teamData), parse_float=Decimal)
            table.update_item(
                Key={
                    'id': str(teamData['id'])
                },
                UpdateExpression='SET barttorvik = :val',
                ExpressionAttributeValues={
                    ':val': item
                }
            )
        logger.info("DynamoDB table updated with kenpom data")
    except Exception as e:
        logger.error(f"Error updating dynamoDB table: {e}")

def lambda_handler(event, context):
    year = "2024"
    bucket = 'cbb-ai'
    key = 'bt_id.json'
    bt_id = read_file_from_s3(bucket, key)
    bt_id = json.loads(bt_id)
    data = GetBarttorvikData(year,bt_id)
    return {
        'statusCode': 200,
        'body': "data updated"
    }