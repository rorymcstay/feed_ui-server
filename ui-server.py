import logging
from logging.config import dictConfig
import os
import json
from feed.settings import *
from feed.settings import logger_settings_dict



if __name__ == '__main__':
    dictConfig(logger_settings_dict('root'))

    logging.getLogger('conn').setLevel('WARNING')
    logging.getLogger('urllib3').setLevel('WARNING')
    logging.getLogger('parser').setLevel('WARNING')
    logging.getLogger('metrics').setLevel('WARNING')
    logging.getLogger('connectionpool').setLevel('WARNING')
    logging.getLogger('kafka').setLevel('WARNING')
    logging.getLogger('service').setLevel('DEBUG')
    logging.getLogger('config').setLevel('WARNING')
    logging.info("####### Environment #######")
    logging.debug(logger_settings_dict(__name__))
    logging.info("\n".join([f'{key}={os.environ[key]}' for key in os.environ]))
    logging.info("mongo : {}".format(json.dumps(mongo_params, indent=4, sort_keys=True)))
    logging.info("kafka : {}".format(json.dumps(kafka_params, indent=4, sort_keys=True)))
    logging.info("router: {}".format(json.dumps(routing_params, indent=4, sort_keys=True)))
    logging.info("nanny: {}".format(json.dumps(nanny_params, indent=4, sort_keys=True)))
    logging.info("database: {}".format(json.dumps(database_parameters, indent=4, sort_keys=True)))
    logging.info("feed : {}".format(json.dumps(feed_params, indent=4, sort_keys=True)))
    logging.info("authn: {}".format(json.dumps(authn_params, indent=4, sort_keys=True)))

    from src.main.app import app
    logging.info(app.url_map)
    app.run(port=os.getenv("FLASK_PORT", os.getenv("UISERVER_PORT", 5004)), host=os.getenv('UISERVER_HOST'))
