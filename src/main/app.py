from flask import Flask
from flask_cors import CORS

from feed.service import Client
from feed.chainsessions import init_app

from src.main.scheduler import ScheduleManager
from src.main.tables import TableManager
from src.main.feedmanager import FeedManager
from src.main.samplepages import SamplePages
from src.main.actionstatic import ActionsStaticData

from src.main.usersession import User
from feed.chainsessions import AuthorisedChainSession



app = init_app(User, sessionManager=AuthorisedChainSession)

app.config['APPLICATION_ROOT'] = '/api'

CORS(app)

FeedManager.register(app, route_prefix='/api')
ScheduleManager.register(app, route_prefix='/api')
TableManager.register(app , route_prefix='/api')
SamplePages.register(app, route_prefix='/api')
ActionsStaticData.register(app, route_prefix='/api')
