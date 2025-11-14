from flask import Blueprint, render_template
from utilscbb.espn import get_scores,get_espn_boxscore

boxscore = Blueprint('boxscore', __name__)


@boxscore.route('/boxscore/<gameId>/<date>')
def get_boxscore(gameId,date):
    scores = get_scores(date)
    score = scores[gameId]
    homeData, awayData, lastPlay = get_espn_boxscore(gameId)
    return render_template('boxscore_new.html', score=score, homeStats=awayData, awayStats=homeData, lastPlay=lastPlay, homeTeamStats=None, awayTeamStats=None)