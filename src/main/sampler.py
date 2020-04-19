import requests as r
from flask_classy import FlaskView
from feed.settings import routing_params
from flask import Response
import json
from feed.logger import getLogger


logging = getLogger(__name__)

class Sampler(FlaskView):

    def getSampleUrl(self,name):
        req = r.get("http://{host}:{port}/routingcontroller/getResultPageUrl/{name}".format(name=name, **routing_params))
        logging.debug(f'got {req.status_code} from router, exampleUrl={req.text}')
        data = {"url": req.text}
        return Response(json.dumps(data), status=200, mimetype='application/json')

