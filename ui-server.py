import logging
from feed.logger import initialiseSrcLogger
import os
from flask import Flask
from flask_cors import CORS
import json

from feed.service import Client

from src.main.feedmanager import FeedManager
from src.main.scheduler import ScheduleManager
from src.main.tables import TableManager
from src.main.sampler import Sampler

from feed.settings import *



app = Flask(__name__)

logging.info("####### Environment #######")
logging.info("mongo : {}".format(json.dumps(mongo_params, indent=4, sort_keys=True)))
logging.info("kafka : {}".format(json.dumps(kafka_params, indent=4, sort_keys=True)))
logging.info("database: {}".format(json.dumps(database_parameters, indent=4, sort_keys=True)))
logging.info("feed : {}".format(json.dumps(feed_params, indent=4, sort_keys=True)))
logging.info("persistence: {}".format(json.dumps(persistence_params, indent=4, sort_keys=True)))
logging.info("summarizer: {}".format(json.dumps(summarizer_params, indent=4, sort_keys=True)))

initialiseSrcLogger()

CORS(app)
FeedManager.register(app )
ScheduleManager.register(app )
TableManager.register(app )
Sampler.register(app)

print(app.url_map)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv("FLASK_PORT", 5004))
