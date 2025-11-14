from flask import Blueprint, render_template
import warnings
from constants import constants
from utilscbb.schedule import get_team_schedule

# Ignore all warnings
warnings.filterwarnings("ignore")


schedule = Blueprint('schedule', __name__)



@schedule.route('/schedule/<id>' , methods=['GET','POST'])
def post_schedule(id):
    data = get_team_schedule(id, constants.YEAR, constants.NET_RANK_BOOL)
    return render_template('schedule_new.html', data = data)


