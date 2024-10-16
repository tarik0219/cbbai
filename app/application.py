from flask import Flask
from home.home import home
from schedule.schedule import schedule
from conference.conference import conference
from predict_api.predict_api import predict_api
from flask_bootstrap import Bootstrap
from scores.scores import bs
from predict.predict import predict
from datetime import datetime, timedelta


application = Flask(__name__, static_folder='static') 
Bootstrap(application)
application.config['SECRET_KEY'] = 'secret'

application.register_blueprint(home, url_prefix='/')
application.register_blueprint(schedule)
application.register_blueprint(conference)
application.register_blueprint(predict_api)
application.register_blueprint(bs)
application.register_blueprint(predict)

@application.context_processor
def inject_now():
    if (datetime.utcnow() - timedelta(hours = 9)).date() < datetime.strptime("20241104", '%Y%m%d').date():
        date = "2024-11-04"
    elif (datetime.utcnow() - timedelta(hours = 9)).date() > datetime.strptime("20250407", '%Y%m%d').date():
        date = "2025-04-07"
    else:
        date = (datetime.utcnow() - timedelta(hours = 9)).strftime('%Y-%m-%d')
    return {'now': date}


if __name__ == '__main__':
    application.run(debug=True)