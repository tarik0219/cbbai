import requests
import boto3
from datetime import datetime, timedelta
from aws_lambda_powertools import Logger
from utilscbb.dynamo import get_team_data_name


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
        competition = game['competitions'][0]
        siteType = competition.get('neutralSite')
        logger.info("Game details", gameID = gameID, siteType = siteType)

        # Team 1
        team1 = competition['competitors'][0]
        homeTeam = team1['team']['displayName']
        #call cbb-ai dynamo table and get the average stats for the home team
        homeData = get_team_data_name(homeTeam)
        # if homeData is not a blank list
        if homeData:
            homeAverage = homeData[0]['average']
        else:
            homeAverage = {}
        logger.info("Home team data", homeData = homeData)

        # Team 2
        team2 = competition['competitors'][1]
        awayTeam = team2['team']['displayName']
        #call cbb-ai dynamo table and get the average stats for the away team
        awayData = get_team_data_name(awayTeam)
        # if awayData is not a blank list
        if awayData:
            awayAverage = awayData[0]['average']
        else:
            awayAverage = {}
        logger.info("Away team data", awayData = awayData)

        # Game details
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
                    "overUnder":oddsResponse['items'][0]['overUnder'],
                    "homeData":homeAverage,
                    "awayData":awayAverage,
                    "siteType":siteType
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
                        'overUnder': str(odds['overUnder']),
                        'homeData': odds['homeData'],
                        'awayData': odds['awayData'],
                        'siteType': odds['siteType']
                    }
                )
        logger.info(f"Added odds to dynamoDB", numOdds = len(oddsResponseList))
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

    todayDate = datetime.now().strftime("%Y%m%d")
    oddsResponseMap, oddsResponseList = get_odds_by_date(todayDate)
    batch_add_odds_dynamo(oddsResponseList)
    return {
        'statusCode': 200,
        'body': "success"
    }

if __name__ == "__main__":
    lambda_handler(None, None)