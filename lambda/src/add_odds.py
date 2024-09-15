import requests
import boto3
from datetime import datetime, timedelta
from aws_lambda_powertools import Logger


logger = Logger(service="cbb-ai")


def get_odds_by_game_id(gameID):
    try:
        url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{gameID}/competitions/{gameID}/odds?="
        response = requests.request("GET", url).json()
    except Exception as e:
        logger.error(f"Error getting api response for odds for game", gameID = gameID)
        response = []
    return response

def get_odds_by_date(date):
    try:
        url = 'http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard'
        response = requests.get(url,params={'limit':'500','groups':'50','dates': str(date)}).json()
        logger.info("Number of games for date", date = date, numGames = len(response['events']))
    except Exception as e:
        logger.error(f"Error getting odds for date", date = date)
        response = []
    oddsResponseMap = {}
    oddsResponseList = []
    for game in response['events']:
        gameID = game['id']
        oddsResponse = get_odds_by_game_id(gameID)
        if len(oddsResponse['items']) > 0:
            try:
                oddsResponseMap[gameID] = {
                    "spread":oddsResponse['items'][0]['spread'],
                    "overUnder":oddsResponse['items'][0]['overUnder']
                }
                oddsResponseList.append({
                    "gameID":gameID,
                    "spread":oddsResponse['items'][0]['spread'],
                    "overUnder":oddsResponse['items'][0]['overUnder']
                })
            except:
               logger.warning(f"Warning no odds for game", gameID = gameID)
    return oddsResponseMap, oddsResponseList


def batch_add_odds_dynamo(oddsResponseList):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('odds')
        with table.batch_writer() as batch:
            for odds in oddsResponseList:
                batch.put_item(
                    Item={
                        'gameID': str(odds['gameID']),
                        'spread': str(odds['spread']),
                        'overUnder': str(odds['overUnder'])
                    }
                )
    except Exception as e:
        logger.error(f"Error adding odds to dynamoDB", e = e)

def generate_dates():
    start_date = datetime.strptime('2024-03-05', '%Y-%m-%d')
    end_date = datetime.strptime('2024-04-09', '%Y-%m-%d')
    date_list = []
    
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y%m%d'))
        current_date += timedelta(days=1)
    
    return date_list

def lambda_handler(event, context):
    #get odds from date 11/01/2023 to 04/09/2024 in format YYYYMMDD
    #create list of dates from 11/08/2023 to 04/09/2024 in format YYYYMMDD
    # dates = generate_dates()
    # for date in dates:
    #     oddsResponseMap, oddsResponseList = get_odds_by_date(date)
    #     batch_add_odds_dynamo(oddsResponseList)

    todayDate = datetime.datetime.now().strftime("%Y%m%d")
    oddsResponseMap, oddsResponseList = get_odds_by_date(todayDate)
    batch_add_odds_dynamo(oddsResponseList)
    return {
        'statusCode': 200,
        'body': "success"
    }