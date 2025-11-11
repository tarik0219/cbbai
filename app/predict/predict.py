from flask import Blueprint, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField
from utilscbb.dynamo import get_all_team_data, get_team_data_name
from utilscbb.predictAPI import call_prediction_endpoint
import random
from werkzeug.datastructures import MultiDict



predict = Blueprint('predict', __name__)

class PredictGame(FlaskForm):
    data = get_all_team_data()
    teams = []
    for team in data:
        try:
            teams.append(team['teamName'])
        except:
            pass
    teams.sort()
    hometeam = SelectField('Home Team', choices = teams)
    awayteam = SelectField('Away Team', choices = teams)
    neutral = SelectField('Neutral Venue', choices = ['No','Yes'])

@predict.route('/predict',methods=['GET','POST'])
def predict_game():
    if request.method == 'GET':
        form = PredictGame(formdata=MultiDict({'hometeam': random.choice(PredictGame.teams), 'awayteam': random.choice(PredictGame.teams)}))
    else:
        form = PredictGame()
    if request.method == 'POST':
        if form.validate_on_submit():
            hometeam = request.form.get('hometeam')
            awayteam = request.form.get('awayteam')
            neutral = request.form.get('neutral')
            return redirect(url_for("predict.predictresults", hometeam = hometeam, awayteam=awayteam, neutral = neutral))
    return render_template("predict.html", form = form)

#change each dict item from Decimal to float
def change_dict(data):
    for key,item in data.items():
        data[key] = float(item)
    return data

@predict.route('/predict/<hometeam>/<awayteam>/<neutral>', methods=['GET'])
def predictresults(hometeam,awayteam,neutral):
    if neutral == "Yes":
        neutral = True
    else:
        neutral = False
    homeData = get_team_data_name(hometeam)[0]
    awayData = get_team_data_name(awayteam)[0]
    data = {
        "games":[
            {
                "homeData":change_dict(homeData['average']),
                "awayData":change_dict(awayData['average']),
                "neutralSite":neutral
            }
        ]
    }
    print(data)
    response = call_prediction_endpoint(data)
    homeScore = response[0]['homeScore']
    awayScore = response[0]['awayScore']
    prob = response[0]['prob']
    prob = prob * 100
    return render_template("predictResults.html", homeData = homeData, awayData = awayData, homeScore = homeScore, awayScore = awayScore, prob = prob)


