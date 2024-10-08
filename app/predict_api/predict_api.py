from pydantic import BaseModel
from flask import Blueprint, jsonify, request
from typing import List
from utilscbb.predict import make_prediction_api
import os
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

predict_api = Blueprint('predict_api', __name__)

scoresFile = os.path.join(os.getcwd(), "models/scores.pkl")
probFile = os.path.join(os.getcwd(), "models/prob.pkl")

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