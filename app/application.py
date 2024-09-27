from flask import Flask
from home.home import home
from schedule.schedule import schedule
from conference.conference import conference
from flask_bootstrap import Bootstrap


application = Flask(__name__, static_folder='static') 
Bootstrap(application)
application.config['SECRET_KEY'] = 'secret'

application.register_blueprint(home, url_prefix='/')
application.register_blueprint(schedule)
application.register_blueprint(conference)


if __name__ == '__main__':
    application.run(debug=True)