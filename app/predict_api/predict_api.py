from pydantic import BaseModel
from flask import Blueprint, jsonify, request
from typing import List
from utilscbb.predict import make_prediction_api
import os
import numpy as np
import pandas as pd
import joblib
import pickle
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

predict_api = Blueprint('predict_api', __name__)

scoresFile = os.path.join(os.getcwd(), "models/scores.pkl")
probFile = os.path.join(os.getcwd(), "models/prob.pkl")

tournamentFile = os.path.join(os.getcwd(), "models/tournament_model_v2.pkl")
seedFile = os.path.join(os.getcwd(), "models/seed_model_v2.pkl")
tournamentModel = pickle.load(open(tournamentFile, 'rb'))
seedModel = pickle.load(open(seedFile, 'rb'))

class TeamData(BaseModel):
    TempoRating: float
    defRating: float
    offRating: float

class PredictModel (BaseModel):
    homeData: TeamData
    awayData: TeamData
    neutralSite: bool

class PredictModelList (BaseModel):
    games: List[PredictModel]

class TournamentList (BaseModel):
    teams: List[TeamData]

class TeamData(BaseModel):
    win: int
    loss: int
    q1w: int
    q1l: int
    q2w: int
    q2l: int
    q3w: int
    q3l: int
    q4w: int
    q4l: int
    rank: int

@predict_api.route('/tournamentList', methods=['POST'])
def tournament_teams():
    try:
        data = request.get_json()
        response = []
        for team in data['teams']:
            win = team['win']
            loss = team['loss']
            q1w = team['q1w']
            q1l = team['q1l']
            q2w = team['q2w']
            q2l = team['q2l']
            q3w = team['q3w']
            q3l = team['q3l']
            q4w = team['q4w']
            q4l = team['q4l']
            rank = team['rank']
            input = pd.DataFrame([[win, loss, q1w, q1l, q2w, q2l, q3w, q3l, q4w, q4l, rank]])
            tournamentOdds = tournamentModel.predict_proba(input)[:, 1][0]
            seed = seedModel.predict(input)[0]
            response.append({'tournamentOdds':tournamentOdds,'seed':seed})
        return jsonify(response)
    except Exception as e:
        return jsonify({"error":"Invalid JSON" + str(e)}), 400

#Predict Games
@predict_api.route('/predictList', methods=['POST'])
def predict_games():
    try:
        #PredictModelList(**request.get_json())
        data = request.get_json()
        print(data)
        response = []
        for game in data['games']:
            homeScore,awayScore,prob = make_prediction_api(game['homeData'],game['awayData'],game['neutralSite'])
            print(homeScore,awayScore,prob)
            response.append({'homeScore':homeScore,'awayScore':awayScore,'prob':prob})
        return jsonify(response)
    except Exception as e:
        return jsonify({"error":"Invalid JSON" + str(e)}), 400