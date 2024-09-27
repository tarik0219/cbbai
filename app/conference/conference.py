from flask import Blueprint, render_template
from utilscbb.dynamo import get_all_team_data
from utilscbb.espn import call_espn_team_standings_api
from constants.constants import YEAR

conference = Blueprint('conference', __name__)


def get_teams(conf):
    conf_teams = []
    teams = get_all_team_data()
    for team in teams:
        if team['conference'] == conf:
            conf_teams.append(team)
    return conf_teams

def get_all_conf_data():
    teams = get_all_team_data()
    conf_data = {}
    for item in teams:
        if item['conference'] in conf_data:
            conf_data[item['conference']]['count'] += 1
            conf_data[item['conference']]['rank'] += item['ranks']['rank']
            conf_data[item['conference']]['average'] = conf_data[item['conference']]['rank']/conf_data[item['conference']]['count']
            if conf_data[item['conference']]['max'] < item['ranks']['rank']:
                conf_data[item['conference']]['max'] = item['ranks']['rank']
            if conf_data[item['conference']]['min'] > item['ranks']['rank']:
                conf_data[item['conference']]['min'] = item['ranks']['rank']
        elif item['conference'] != "IND":
            conf_data[item['conference']] ={
                "count":1,
                "rank":item['ranks']['rank'],
                "average":item['ranks']['rank'],
                "max":item['ranks']['rank'],
                "min":item['ranks']['rank'],
            }
    data = []
    for key,item in conf_data.items():
        item['conference'] = key
        data.append(item)
    return data


@conference.route('/conference/<conf>')
def conference_stadnings(conf):
    data = get_teams(conf)
    standings = call_espn_team_standings_api(YEAR)
    for count,team in enumerate(data):
        data[count]['record'] = standings[team['id']]
    data.sort(key=lambda x: (x["record"]['conferenceStanding']))
    print(data)
    return render_template('conference.html', data=data, conference = conf)

@conference.route('/conference')
def conference_rank():
    data = get_all_conf_data()
    data.sort(key=lambda x: x["average"], reverse=False)
    return render_template('conferenceRanks.html', data=data)
