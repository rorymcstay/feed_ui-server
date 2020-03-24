from feed.logger import logger as logging
import os
from flask import Flask
from flask_cors import CORS
import json

from feed.service import Client

from src.main.feedmanager import FeedManager
from src.main.scheduler import ScheduleManager
from src.main.search import Search
from src.main.tables import TableManager
from src.main.mappermanager import MapperManager

from feed.settings import *



app = Flask(__name__)

logging.info("####### Environment #######")
logging.info("mongo : {}".format(json.dumps(mongo_params, indent=4, sort_keys=True)))
logging.info("kafka : {}".format(json.dumps(kafka_params, indent=4, sort_keys=True)))
logging.info("hazelcast : {}".format(json.dumps(hazelcast_params, indent=4, sort_keys=True)))
logging.info("database: {}".format(json.dumps(database_parameters, indent=4, sort_keys=True)))
logging.info("feed : {}".format(json.dumps(feed_params, indent=4, sort_keys=True)))
logging.info("persistence: {}".format(json.dumps(persistence_params, indent=4, sort_keys=True)))
logging.info("summarizer: {}".format(json.dumps(summarizer_params, indent=4, sort_keys=True)))


Client('commands', **command_params)
CORS(app)
Search.register(app)
FeedManager.register(app )
ScheduleManager.register(app )
TableManager.register(app )
MapperManager.register(app)

print(app.url_map)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv("FLASK_PORT", 5004))
