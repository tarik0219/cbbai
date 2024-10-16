from datetime import datetime
from dateutil import tz
from utilscbb.dynamo import get_all_team_data, get_odds_data
from utilscbb.predict import make_prediction_api
from utilscbb.espn import call_espn_scores_api


def convertDateTime(dateTime):
    from_zone = tz.gettz("Africa/Accra")
    to_zone = tz.gettz('America/New_York')
    test = dateTime
    test = test.split("T")[0] + " " + test.split("T")[1].split("Z")[0]
    utc = datetime.strptime(test, "%Y-%m-%d %H:%M")
    utc = utc.replace(tzinfo=from_zone)
    eastern = str(utc.astimezone(to_zone))
    date = eastern.split(" ")[0]
    time = eastern.split(" ")[1].split("-")[0]
    return date, time


def get_team_data(teamID, teamsData):
    if teamID in teamsData:
        return teamsData[teamID]
    else:
        return {}

def get_prediction(homeData, awayData, neutralSite):
    if (len(homeData) == 0) or (len(awayData) == 0):
        return None, None, None
    homeScore,awayScore,prob = make_prediction_api(homeData['average'], awayData['average'], neutralSite)
    return homeScore,awayScore,prob

def add_line_data(oddsData, gameID):
    if gameID in oddsData:
        game = oddsData[gameID]
        game['spread']['S'] = float(game['spread']['S'])
        game['overUnder']['S'] = float(game['overUnder']['S'])
        return game
    else:
        return {'spread': {'S': None}, 'overUnder': {'S': None}}
                
def get_teams_data_dict(teamsData):
    teamsDataDict = {}
    for team in teamsData:
        teamsDataDict[team['id']] = team
    return teamsDataDict

def get_odds_data_dict(espnScores):
    gameIds = list(espnScores.keys())
    oddsData = get_odds_data(gameIds)
    oddsDataDict = {}
    for game in oddsData:
        oddsDataDict[game['gameID']['S']] = game
    return oddsDataDict

def get_scores_data(date):
    espnScores = call_espn_scores_api(date)
    teamsData = get_all_team_data()
    teamsDataDict = get_teams_data_dict(teamsData)
    espnScoresList = []
    oddsData = get_odds_data_dict(espnScores)
    for gameId,game in espnScores.items():
        homeData = get_team_data(game['homeTeamId'], teamsDataDict)
        awayData = get_team_data(game['awayTeamId'], teamsDataDict)
        if game['status'] == 'post':
            homeScore, awayScore, prob = None, None, None
        else:
            homeScore,awayScore,prob = get_prediction(homeData, awayData, game['siteType'])
        odds = add_line_data(oddsData, gameId)
        game.update({
            "homeData": homeData,
            "awayData": awayData,
            "homeScorePredict": homeScore,
            "awayScorePredict": awayScore,
            "prob": prob,
            "spread": odds['spread']['S'],
            "overUnder": odds['overUnder']['S']
        })
        espnScoresList.append(game)
    return  espnScoresList