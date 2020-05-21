from flask import Flask
from flask_cors import CORS

from feed.service import Client

from src.main.scheduler import ScheduleManager
from src.main.tables import TableManager
from src.main.feedmanager import FeedManager


app = Flask(__name__)


CORS(app)

FeedManager.register(app )
ScheduleManager.register(app )
TableManager.register(app )
