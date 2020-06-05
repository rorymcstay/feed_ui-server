from feed.logger import logger as logging
from datetime import datetime

from time import time

from docker.errors import APIError
from docker.models.containers import Container
from kafka import KafkaClient
from kafka.errors import TopicAlreadyExistsError
import json
import os
import requests as r

from flask import Response, request, session
from flask_classy import FlaskView, route

import pymongo
from pymongo.database import Database

from feed.settings import mongo_params


class FeedManager(FlaskView):
    def __init__(self):
        self.mongoClient = pymongo.MongoClient(**mongo_params)
        self.forms: Database = self.mongoClient[os.getenv("CHAIN_DB", "actionChains")]['parameterForms']
        self.feeds: Database = self.mongoClient[os.getenv("CHAIN_DB", "actionChains")]['actionChainDefinitions']
        self.parameterSchemas = self.forms['parameterSchemas']
        # TODO This is called multiple times, should make it so that it is only once. 
        # Take this as the beginnings of the kafka interface
        self.feed_params: Database = self.mongoClient[os.getenv("PARAMETER_DATABASE", "params")]

    def getParameter(self, component, feedName):
        """
        return the parameter for the service component

        <example1>

            #request: /leader/donedeal

            #response:
            {
                "name": "donedeal",
                "next_page_xpath": "//*[@id]",
                "next_button_text": "next",
                "next_button_css": ".icon-nav_arrow_right",
                "result_stub": "https://www.donedeal.co.uk/cars-for-sale/",
                "wait_for": ".cad-header",
                "base_url": "https://donedeal.co.uk/cars",
                "result_stream": {
                  "class": "card-item",
                  "single": false
                },
                "page_url_param": "sort"
            }
        <example1/>

        :param component:
        :param name:
        :return:
        """
        if feedName == 'undefined':
            return Response(json.dumps({}), mimetype='application/json', status=200)
        params = self.feed_params[component].find_one(filter={"name": feedName})
        if params is None:
            return Response(status=404)
        params.pop("_id")
        return Response(json.dumps(params), mimetype="application/json")

    def getParameterTypes(self):
        """
        <example1>
            #request: /getParameterTypes/
            #response:
                [ "leader", "router", "mapper", "persistence", "worker", "leader"]
        <example1/>
        :return:
        """
        c = self.parameterSchemas.find({})

        data = [param.get("name") for param in c]
        return Response(json.dumps(data), mimetype="application/json")

    def refreshHistory(self, name):
        session["router"].delete(f'/routingcontroller/clearHistory/{name}')
        return 'ok'

    @route('setActionChain/', methods=['PUT'])
    def setActionChain(self):
        logging.debug(f'Requesting nanny to set {request.get_json()}')
        logging.debug(f'data = {request.data}')
        resp = session["nanny"].put('/actionsmanager/setActionChain/', resp=True, payload=request.get_json())
        return Response(json.dumps(resp), mimetype='application/json')

    @route('clearActionErrorReports/<string:actionChainName>', methods=['DELETE'])
    def clearActionErrorReports(self, actionChainName):
        session["nanny"].delete(f'/actionsmanager/clearActionErrorReports/{actionChainName}')
        return 'ok'

    def findActionErrorReports(self, actionChainName, position):
        reports = session["nanny"].get(f'/actionsmanager/findActionErrorReports/{actionChainName}/{position}', resp=True)
        return Response(json.dumps(reports), mimetype='application/json')

    def disableFeed(self, name):
        session["nanny"].get(f'/runningmanager/disableFeed/{name}')
        return 'ok'

    def getActionChains(self):
        chains = session["nanny"].get(f'/actionsmanager/getUserActionChains/', resp=True, error=[])
        return Response(json.dumps(chains), mimetype='application/json')

    def getActionChain(self, name):
        chains = session["nanny"].get(f'/actionsmanager/getActionChain/{name}', resp=True, error=[])
        return Response(json.dumps(chains), mimetype='application/json')

    def getStatus(self, name):
        status = session["nanny"].get(f'/runningmanager/getStatus/{name}', resp=True, error=None)
        return Response(json.dumps(status), mimetype='application/json')

    def getParameterSchema(self, parameterName):
        """
        <example1>
            #request: /getParameterSchema/worker
            #response:
            {
                "name": "worker",
                "value": {
                    "title": "Worker Stream Config",
                    "description": "specifies what the worker should send out",
                    "type": "object",
                    "properties": {
                        "class": {
                            "type": "string",
                            "default": null,
                            "title": "name of class to stream"
                        },
                        "single": {
                        "type": "boolean",
                        "default": true,
                        "title": "is the item unique"
                    },
                    "page_ready": {
                        "type": "string",
                        "default": "img",
                        "title": "the class of the item to wait for"
                    }
                }
            }
            <example1/>

        :param parameterName:
        :return:
        """
        parameter = self.parameterSchemas.find_one({"name": parameterName})
        if parameter is None:
            return Response(f'no parameter schema found for {parameterName}', status=404)
        val = parameter['value']
        return Response(json.dumps(val), mimetype="application/json")

    @route("/setParameter/<string:collection>/<string:name>", methods=['PUT'])
    def setParameter(self, collection, name=None):
        """
        <example1>
            #request: /setParameter/worker/donedeal
            #payload: {
                "name": "donedeal",
                "next_page_xpath": "//*[@id]",
                "next_button_text": "next",
                "next_button_css": ".icon-nav_arrow_right",
                "result_stub": "https://www.donedeal.co.uk/cars-for-sale/",
                "wait_for": ".cad-header",
                "base_url": "https://donedeal.co.uk/cars",
                "result_stream": {
                  "class": "card-item",
                  "single": false
                },
                "page_url_param": "sort"
            }
            #response: "ok"
        <example1/>
        :param collection:
        :param name:
        :return:
        """
        value = request.get_json()
        param: dict = self.feed_params[collection].find_one({"name": name})
        value.update({"name": name})
        old = param
        if param is not None:
            self.feed_params[collection].replace_one(filter={"name": name}, replacement=value)
            old["name"] = "{}_{}".format(name, datetime.now().strftime("%d%m%Y"))
            old.pop("_id")
            if os.getenv('PARAM_VERSIONING_ON', False):
                self.feed_params[collection].insert(old)
        else:
            self.feed_params[collection].insert_one(value)
        return Response("ok", status=200)

    def getFeeds(self):
        """
        <example1>
            #request: /getFeeds/
            #response: ["donedeal", "pistonheads"]
        <example1/>
        :return:
        """
        c = self.feeds.find({})
        data = [param.get("name") for param in c]
        return Response(json.dumps(data), mimetype="application/json")

    def startFeed(self, feedName, mode):
        """
        # TODO used anymore, clean up ui usage.
        <example1>
             #request: /startFeed/donedeal
             #response: {"status": true}
        <example1/>
        :param feedName:
        :param mode: run mode, one of 'run', 'test', 'single'
        :return:
        """
        return Response(json.dumps({"status": True}), status=200)

    def stopFeed(self, feedName):
        """
        <example1>
             #request: /stopFeed/donedeal
             #response: "ok"
        <example1/>
        :param feedName:
        :return:
        """
        return "ok"

    def feedStatus(self, feedName):
        """
        <example1>
             #request: /feedStatus/donedeal
             #response: {"status": true}
        <example1/>
        :param feedName:
        :return:
        """
        req = session["nanny"].get(f'/runningmanager/getStatus/{feedName}', resp=True)
        stat = req.json()
        return Response(json.dumps(stat), mimetype='application/json')

