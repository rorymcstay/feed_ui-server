import logging
from logging.config import dictConfig
import os
import json
from feed.settings import *


if __name__ == '__main__':
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s]%(thread)d: %(module)s - %(levelname)s - %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': os.getenv("LOG_LEVEL", "INFO"),
            'handlers': ['wsgi']
        }
    })

    logging.info("####### Environment #######")
    logging.info("\n".join([f'{key}={os.environ[key]}' for key in os.environ]))
    logging.info("mongo : {}".format(json.dumps(mongo_params, indent=4, sort_keys=True)))
    logging.info("kafka : {}".format(json.dumps(kafka_params, indent=4, sort_keys=True)))
    logging.info("database: {}".format(json.dumps(database_parameters, indent=4, sort_keys=True)))
    logging.info("feed : {}".format(json.dumps(feed_params, indent=4, sort_keys=True)))
    logging.info("persistence: {}".format(json.dumps(persistence_params, indent=4, sort_keys=True)))
    logging.info("summarizer: {}".format(json.dumps(summarizer_params, indent=4, sort_keys=True)))

    from src.main.app import app
    logging.info(app.url_map)
    app.run(port=os.getenv("FLASK_PORT", os.getenv("UISERVER_PORT", 5004)), host=os.getenv('UISERVER_HOST'))
