from feed.logger import logger as logging
from datetime import datetime

from time import time

import docker
from docker.errors import APIError
from docker.models.containers import Container
from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaClient
from kafka.errors import TopicAlreadyExistsError
import json
import os
import requests as r

from flask import Response, request
from flask_classy import FlaskView, route

import pymongo
from pymongo.database import Database

from feed.settings import mongo_params, kafka_params, feed_params, summarizer_params


class FeedManager(FlaskView):
    def __init__(self):
        self.dockerClient = docker.from_env()
        self.mongoClient = pymongo.MongoClient(**mongo_params)
        self.forms: Database = self.mongoClient[os.getenv("FORM_DATABASE", "forms")]
        self.feeds: Database = self.mongoClient[os.getenv("PARAMETER_DATABASE", "params")]
        self.parameter_stats: Database = self.mongoClient[os.getenv("PARAM_STATS_DATABASE", "params_stats")]
        self.parameterSchemas = self.forms['parameterSchemas']
        self.admin = KafkaAdminClient(**kafka_params)
        logging.info(f'bootstrap_servers: {kafka_params.get("bootstrap_servers")} kafka: {json.dumps(kafka_params, indent=4)}')
        self.kafkaClient = KafkaClient(**kafka_params)
        self.feed_params: Database = self.mongoClient[os.getenv("PARAMETER_DATABASE", "params")]
        self.feed_ports = {name.get("name"): feed_params['base_port']+i for (i, name) in enumerate(self.feeds["leader"].find({}))}

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

    def getParameterStatus(self, feedName):
        """
        Get the number of fails a component parameter value has

        <example1>
            #request: GET getParameterStatus/donedeal

            #response:
            {
                "errors": errors,
                "name": parameterName
            }
        <example1/>

        @

        :param feedName:
        :return:
        """
        c = self.parameterSchemas.find({})
        payload = []
        for parameterName in [param.get("name") for param in c]:
            errors = self.parameter_stats[parameterName].count({"name": feedName})
            status = {
                "errors": errors,
                "name": parameterName
            }
            payload.append(status)
        return Response(json.dumps(payload), mimetype='application/json')

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
        c = self.feeds["leader"].find({})
        data = [param.get("name") for param in c]
        return Response(json.dumps(data), mimetype="application/json")

    def newFeed(self, feedName):
        """
        <example>
            #request: /newFeed/donedeal
            #response: ok
        <example/>
        :param feedName:
        :return:
        """
        port = len(self.feed_ports)
        self.feed_ports.update({feedName: feed_params['base_port'] + port})
        c = self.feeds["leader"].find({"name": feedName})
        if any(val == feedName for val in c):
            pass
        else:
            self.feeds["leader"].insert_one({"name": feedName})
        return "ok"

    def startFeed(self, feedName, mode):
        """
        <example1>
             #request: /startFeed/donedeal
             #response: {"status": true}
        <example1/>
        :param feedName:
        :param mode: run mode, one of 'run', 'test', 'single'
        :return:
        """
        logging.info("starting feed {}".format(feedName))
        parameterSets = self.feeds.list_collection_names(include_system_collections=False)
        notSet = []
        for set in parameterSets:
            if self.feeds[set].find_one({"name": feedName}) is None:
                notSet.append(set)
        if len(notSet):
            logging.info(f'some parameters not set for {feedName}')
            payload = {"notSet": notSet, "status": False}
            return Response(json.dumps(payload), mimetype='application/json')
        else:
            try:
                queues_to_make = []
                queues_to_make.append(
                    NewTopic(name="{}-results".format(feedName), num_partitions=1, replication_factor=1))
                queues_to_make.append(
                    NewTopic(name="{}-items".format(feedName), num_partitions=1, replication_factor=1))
                self.admin.create_topics(queues_to_make)
            except TopicAlreadyExistsError:
                pass
            try:
                feed = self.dockerClient.containers.get(feedName)
                logging.info(
                    f'starting {feedName} worker container from image {feed.image.id}')
                feed.start()
            except APIError as e:
                services = ["FLASK", "NANNY", "ROUTER", "KAFKA", "BROWSER"]
                image = self.dockerClient.images.get(feed_params['image'])
                all_env = list(map(lambda key: '{}={}'.format(*key), os.environ.items()))
                env_vars = list(filter(lambda item: any(service in item for service in services), all_env))
                logging.info(f'using environment variables: {env_vars}')
                feed: Container = self.dockerClient.containers.run(image=image,
                                                                   command=f'--{mode}',
                                                                   environment=["NAME={}".format(feedName),
                                                                                f'BROWSER_PORT={self.feed_ports.get(feedName)}'] + env_vars,
                                                                   detach=True,
                                                                   name=feedName,
                                                                   restart_policy={"Name": 'always'} if mode == 'run' else None,
                                                                   network=os.getenv("NETWORK", "feed_default"))
                logging.info(f'created {feedName} on network {os.getenv("NETWORK")} on port {self.feed_ports.get(feedName)} from image {feed.image.id}')
            return Response(json.dumps({"status": True}), status=200)

    def getSampleData(self, name):
        data = r.get("http://{host}:{port}/resultloader/getSampleData/{name}".format(name=name, **summarizer_params))
        payload = data.json()
        ret = {"data":[{"html": str(val)} for val in payload]}
        return Response(json.dumps(ret), mimetype='application/json')

    def stopFeed(self, feedName):
        """
        <example1>
             #request: /stopFeed/donedeal
             #response: "ok"
        <example1/>
        :param feedName:
        :return:
        """
        feed = self.dockerClient.containers.get(feedName)
        feed.stop()
        feed.remove()
        self.admin.delete_topics(["{}-{}".format(feedName, val) for val in ("items", "results")])
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
        try:
            feed = self.dockerClient.containers.get(feedName)
            if feed.status == 'running':
                status = True
            else:
                status = False
        except APIError as e:
            status = False
        return Response(json.dumps({"status": status}), mimetype='application/json')


def loadSuccess(browser):
    timeMax = time() + feed_params.get('time_out', 15)
    while time() < timeMax:
        for line in browser.logs().decode().split('\n'):
            if feed_params['success'] in line:
                return True
    return False
