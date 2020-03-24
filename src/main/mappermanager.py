from feed.logger import logger as logging
from feed.settings import summarizer_params, persistence_params, command_params
from feed.service import Client
import requests as r
import json
from flask_classy import FlaskView
from flask import Response



class MapperManager(FlaskView):

    def __init__(self):
        self.services = {}
        self.running = {'summarizer': False, 'persistence': False}
        self.commandBaseUrl = "http://{host}:{port}/commandmanager".format(**command_params)

    def isRunning(self, service):
        req = r.get(f'{self.commandBaseUrl}/isRunning/{service}')
        return self._to_response(req)

    def _to_response(self,req) -> Response:
        return Response(req.text, mimetype=req.headers.get('Content-Type'), status=req.status_code)

    def startSummarizer(self):
        startFeed = r.get(f'{self.commandBaseUrl}/startService/summarizer'.format(**summarizer_params))
        return self._to_response(startFeed)

    def startMapper(self):
        startMapper = r.get(f'{self.commandBaseUrl}/startService/persistence')
        return self._to_response(startMapper)

