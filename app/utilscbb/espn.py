import requests
from datetime import datetime
from dateutil import tz
import json



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

def get_venue(homeAway, neutralSite):
    if neutralSite:
        return "N"
    elif homeAway == "home":
        return "H"
    else:
        return "Away"


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

def call_espn_schedule_api(teamID, year):
    url = f'https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{teamID}/schedule'
    season_count = 2
    data = []
    while season_count < 4:
        response = requests.get(url,params={'season':year,'seasontype':str(season_count)}).json()
        games = response['events']
        for game in games:
            gameData = {}
            competitionData = game['competitions'][0]
            gameData['date'], gameData['time'] = convertDateTime(game["date"])
            gameData['dateString'] = gameData['date'].replace('-', '')
            gameData['gameId'] = game["id"]
            gameData['neutralSite'] = competitionData.get('neutralSite', False)
            gameData['gameType'] = "REG" if season_count == 2 else "POST"
            gameData['notes'] = competitionData['notes']
            gameData['completed'] = competitionData['status']['type']['completed']
            if competitionData['competitors'][0]["id"] == teamID:
                if gameData['neutralSite']:
                    gameData['venue'] = "N"
                elif competitionData['competitors'][0]["homeAway"] == "home":
                    gameData['venue'] = "H"
                else:
                    gameData['venue'] = "@"
                gameData['score'] = competitionData['competitors'][0].get("score",{}).get("displayValue")
                gameData['opponentScore'] = competitionData['competitors'][1].get("score",{}).get("displayValue")
                gameData['opponentId'] = competitionData['competitors'][1]["id"]
                gameData['opponentName'] = competitionData['competitors'][1]['team']["displayName"]
                if competitionData['competitors'][0]['homeAway'] == "home":
                    gameData['homeTeamId'] = teamID
                else:
                    gameData['homeTeamId'] = competitionData['competitors'][1]["id"]
            else:
                if gameData['neutralSite']:
                    gameData['venue'] = "N"
                elif competitionData['competitors'][0]["homeAway"] == "home":
                    gameData['venue'] = "@"
                else:
                    gameData['venue'] = "H"
                gameData['score'] = competitionData['competitors'][1].get("score",{}).get("displayValue")
                gameData['opponentScore'] = competitionData['competitors'][0].get("score",{}).get("displayValue")
                gameData['opponentId'] = competitionData['competitors'][0]["id"]
                gameData['opponentName'] = competitionData['competitors'][0]["team"]["displayName"]
                if competitionData['competitors'][0]['homeAway'] == "home":
                    gameData['homeTeamId'] = competitionData['competitors'][0]["id"]
                else:
                    gameData['homeTeamId'] = teamID
            if gameData['completed']:
                if int(gameData['opponentScore']) > int(gameData['score']):
                    gameData['result'] = "L"
                elif int(gameData['opponentScore']) < int(gameData['score']):
                    gameData['result'] = "W"
                else:
                    gameData['result'] = None
            else:
                gameData['result'] = None
            data.append(gameData)
        season_count += 1
    return data
    
def get_odds_by_game_id(gameID):
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{gameID}/competitions/{gameID}/odds?="
    response = requests.request("GET", url).json()
    return response


def get_odds_by_date(date):
    url = 'http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard'
    response = requests.get(url,params={'limit':'500','groups':'50','dates': str(date)}).json()
    oddsResponseMap = {}
    oddsResponseList = []
    for game in response['events']:
        oddsResponse = get_odds_by_game_id(game['id'])
        if len(oddsResponse['items']) > 0:
            try:
                oddsResponseMap[game['id']] = {
                    "spread":oddsResponse['items'][0]['spread'],
                    "overUnder":oddsResponse['items'][0]['overUnder']
                }
                oddsResponseList.append({
                    "gameID":game['id'],
                    "spread":oddsResponse['items'][0]['spread'],
                    "overUnder":oddsResponse['items'][0]['overUnder']
                })
            except:
                print("Error getting odds for game: ", game['id'])
    return oddsResponseMap, oddsResponseList

import concurrent.futures

def get_all_odds_by_date(date):
    url = 'http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard'
    response = requests.get(url,params={'limit':'500','groups':'50','dates': str(date)}).json()
    oddsResponseList = []

    def process_game(game):
        oddsResponse = get_odds_by_game_id(game['id'])
        sportsBooks = oddsResponse['items']
        odds = {}
        odds['gameID'] = game['id']
        odds['homeTeamId'] = game['competitions'][0]['competitors'][0]['team']['id']
        odds['awayTeamId'] = game['competitions'][0]['competitors'][1]['team']['id']
        odds['homeTeam'] = game['competitions'][0]['competitors'][0]['team']['displayName']
        odds['awayTeam'] = game['competitions'][0]['competitors'][1]['team']['displayName']
        odds['neutralSite'] = game['competitions'][0].get('neutralSite', False)
        sportsBookMap = {}
        for sportsBook in sportsBooks:
            sportsBookMap[sportsBook['provider']['name']] = sportsBook
        odds['odds'] = sportsBookMap
        return odds

    with concurrent.futures.ThreadPoolExecutor() as executor:
        game_futures = [executor.submit(process_game, game) for game in response['events']]
        for future in concurrent.futures.as_completed(game_futures):
            oddsResponseList.append(future.result())

    return oddsResponseList


def get_half(period):
    if period == 1:
        return "1st"
    elif period == 2:
        return "2nd"
    elif period >= 3:
        return f"{period-2}OT"

def call_espn_scores_api(date):
    # Get ESPN LIVE SCORE DATA
    url = 'http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard'
    response = requests.get(url, params={'limit': '500', 'groups': '50', 'dates': str(date)})
    responseJson = response.json()
    espnScores = {}
    games = responseJson.get('events', {})
    
    if len(games) == 0:
        return espnScores
    
    for game in games:
        competition = game['competitions'][0]
        date = competition['date']
        date, time = convertDateTime(date)

        siteType = competition.get('neutralSite')
        gameId = game['id']
        broadcast = None if len(competition.get('broadcasts',[{}])) == 0 else competition.get('broadcasts',[{}])[0].get('names', [None])[0]

        # Team 1
        team1 = competition['competitors'][0]
        homeTeam = team1['team']['displayName']
        homeTeamId = team1['team']['id']
        homeScore = team1['score']

        # Team 2
        team2 = competition['competitors'][1]
        awayTeam = team2['team']['displayName']
        awayTeamId = team2['team']['id']
        awayScore = team2['score']

        # Game details
        clock = game['status'].get('displayClock')
        period = game['status'].get('period')
        status = game['status']['type'].get('state')

        espnGame = {
            "date": date,
            "time": time,
            "broadcast": broadcast,
            "siteType": siteType,
            "clock": clock,
            "period": period,
            "status": status,
            "homeTeam": homeTeam,
            "homeTeamId": homeTeamId,
            "homeScore": homeScore,
            "awayTeam": awayTeam,
            "awayTeamId": awayTeamId,
            "awayScore": awayScore,
            "half": get_half(period),
            "gameId": gameId
        }
        espnScores[gameId] = espnGame

    return espnScores

def get_espn_boxscore(gameId):
    homeData = []
    awayData = []
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary"
    sports_response = requests.get(url,params={'event':gameId })
    sports_json = json.loads(sports_response.text)
    home = sports_json['boxscore']['players'][1]
    away = sports_json['boxscore']['players'][0]
    labels = home['statistics'][0]['labels']

    for player in home['statistics'][0]['athletes']:
        player_stats = {
            "name" : player['athlete']['displayName'],
            "starter":player['starter']
        }
        stats = player['stats']
        for s, l in zip(stats, labels): 
            if l == "3PT":
                player_stats["TPT"] = s
            else:
                player_stats[l] = s
        homeData.append(player_stats)
    
    for player in away['statistics'][0]['athletes']:
        player_stats = {
            "name" : player.get('athlete', {}).get('displayName', None), 
            "starter":player['starter']
        }
        stats = player['stats']
        for s, l in zip(stats, labels): 
            if l == "3PT":
                player_stats["TPT"] = s
            else:
                player_stats[l] = s
        awayData.append(player_stats)
    lastPlay = {}
    lastPlayResponse = sports_json['plays'][-1]
    teamAID, teamAName = sports_json['boxscore']['teams'][0]['team']['id'], sports_json['boxscore']['teams'][0]['team']['displayName']
    teamBID, teamBName = sports_json['boxscore']['teams'][1]['team']['id'], sports_json['boxscore']['teams'][1]['team']['displayName']

    lastPlayTeam =lastPlayResponse.get('team',None)
    if lastPlayTeam:
        if lastPlayResponse['team']['id'] == teamAID:
            lastPlay['team'] = teamAName
        else:
            lastPlay['team'] = teamBName
    else:
        lastPlay['team'] = None
    lastPlay['text'] = lastPlayResponse['text']
    lastPlay['clock'] = lastPlayResponse['clock']['displayValue']
    return homeData, awayData, lastPlay

def get_scores(date):
    #Get ESPN LIVE SCORE DATA
    try:
        url = 'http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard'
        sports_response = requests.get(url,params={'limit':'500','groups':'50','dates': str(date)})
        sports_json = json.loads(sports_response.text)
        espn = {}
        for game in sports_json['events']:
            date = game['competitions'][0]['date']
            date, time = convertDateTime(date)


            siteType = game['competitions'][0]['neutralSite']
            gameId = game['id']
            try:
                broadcast = game['competitions'][0]['broadcasts'][0]['names'][0]
            except:
                broadcast = None

            #team1
            team_type = game['competitions'][0]['competitors'][0]['homeAway']
            if team_type == 'home':
                homeTeam = game['competitions'][0]['competitors'][0]['team']['displayName']
                homeTeamId = game['competitions'][0]['competitors'][0]['team']['id']
                homeScore = game['competitions'][0]['competitors'][0]['score'] 
            else:
                awayTeam = game['competitions'][0]['competitors'][0]['team']['displayName']
                awayTeamId = game['competitions'][0]['competitors'][0]['team']['id']
                awayScore = game['competitions'][0]['competitors'][0]['score']
            
            #team2    
            team_type = game['competitions'][0]['competitors'][1]['homeAway']
            if team_type == 'home':
                homeTeam = game['competitions'][0]['competitors'][1]['team']['displayName']
                homeTeamId = game['competitions'][0]['competitors'][1]['team']['id']
                homeScore = game['competitions'][0]['competitors'][1]['score']
            else:
                awayTeam = game['competitions'][0]['competitors'][1]['team']['displayName']
                awayTeamId = game['competitions'][0]['competitors'][1]['team']['id']
                awayScore = game['competitions'][0]['competitors'][1]['score']


            #gamedetails
            clock = game['status']['displayClock']
            period = game['status']['period']
            status = game['status']['type']['state']

            espnGame = {
                    "date" : date,
                    "time" : time,
                    "broadcast": broadcast,
                    "siteType": siteType,
                    "clock": clock,
                    "period": period,
                    "status": status,
                    "homeTeam": homeTeam,
                    "homeTeamId": homeTeamId,
                    "homeScore": homeScore,
                    "awayTeam": awayTeam,
                    "awayTeamId": awayTeamId,
                    "awayScore": awayScore,
                    "half":get_half(period)
            }

            espn[gameId] = espnGame


        return espn
    except:
        return {}