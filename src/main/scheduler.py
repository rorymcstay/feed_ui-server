import json
from datetime import datetime, timedelta
from typing import List

import sys
from apscheduler.job import Job
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from docker import client as dockerClient
import requests

from feed.settings import kafka_params, mongo_params, nanny_params
from flask import request, Response
from flask_classy import FlaskView, route
from kafka import KafkaProducer
from feed.logger import getLogger
from src.main.tables import Serialiser

logging = getLogger(__name__)

class ScheduledCollection:

    def __init__(self, feedName, **kwargs):
        self.feedName = feedName
        self.url = kwargs.get("url")
        self.trigger = kwargs.get("trigger")
        self.increment = kwargs.get("increment")
        self.increment_size = kwargs.get("increment_size")
        self.time_out = kwargs.get("time_out")


class JobExecutor:
    docker_client = dockerClient.from_env()
    producer = KafkaProducer(**kafka_params, value_serializer=lambda v: json.dumps(v).encode('utf-8'))

    def startContainer(self, feedName):
        container = self.docker_client.containers.get(feedName)
        container.start()

    def publishUrl(self, feedName, url):
        item = {"url": url, "type": feedName}
        self.producer.send(topic="worker-queue",
                           value=item,
                           key=bytes(url, 'utf-8'))

    def publishActionChain(self, actionChain, queue):
        chainParams = requests.get('http://{host}:{port}/actionsmanager/getActionChain/{name}'.format(name=actionChain, **nanny_params)).json()
        self.producer.send(topic=queue, value=chainParams, key=bytes(chainParams.get('name'), 'utf-8'))


class ScheduleManager(FlaskView):
    scheduler = BackgroundScheduler()
    job_store = MongoDBJobStore(**mongo_params)
    scheduler.add_jobstore(job_store)
    executor = JobExecutor()
    if len(sys.argv) > 1 and sys.argv[1] == '--clear':
        scheduler.remove_all_jobs()
    scheduler.start()
    """
    If you schedule jobs in a persistent job store during your application’s initialization, you MUST define an explicit ID for the job and use replace_existing=True or you will get a new copy of the job every time your application restarts!Tip
    """

    @route("scheduleContainer/<string:feedName>", methods=["PUT"])
    def scheduleContainer(self, feedName):
        logging.info(f'adding job for {feedName} {request.get_json()}')
        job = ScheduledCollection(feedName, **request.get_json())
        if job.trigger == 'date':
            timing = {
                "run_date": datetime.now() + timedelta(**{job.increment: int(job.increment_size)})
            }
        else:
            timing = {
                job.increment: int(job.increment_size),
            }
        self.scheduler.add_job(self.executor.startContainer, job.trigger, args=[feedName], id=feedName,
                               replace_existing=True, **timing)
        return 'ok'

    @route("addJob/<string:feedName>", methods=["PUT"])
    def addJob(self, feedName):
        logging.info(f'adding job for {feedName} {request.get_json()}')
        job = ScheduledCollection(feedName, **request.get_json())
        timing = {
            job.increment: int(job.increment_size),
        } if job.trigger == 'interval' else {
            "run_date": datetime.now() + timedelta(**{job.increment: int(job.increment_size)})
        }
        self.scheduler.add_job(self.executor.publishUrl, job.trigger, args=[feedName, job.url], **timing)
        return 'ok'

    @route("scheduleActionChain/<string:queue>/<string:actionChain>", methods=["PUT"])
    def scheduleActionChain(self, queue, actionChain):
        # TODO: Do check on queue here
        logging.info(f'adding job for {actionChain} {request.get_json()}')
        job = ScheduledCollection(actionChain, **request.get_json())
        if job.increment is '':
            return Response(json.dumps({'job': job.__dict__(), 'reason': "You must specify increment to be one of 'days', 'seconds', or 'hours'"}), status=400)
        timing = {
            job.increment: int(job.increment_size),
        } if job.trigger == 'interval' else {
            "run_date": datetime.now() + timedelta(**{job.increment: int(job.increment_size)})
        }
        self.scheduler.add_job(self.executor.publishActionChain, job.trigger, args=[actionChain, queue], **timing)
        return 'ok'

    def getStatus(self):
        isRunning = self.scheduler.running
        jobs: List[Job] = self.scheduler.get_jobs()
        payload = {"isRunning": isRunning, "jobs": [{'job_name': job.id,
                                                     'next_run': job.next_run_time,
                                                     'trigger': "interval" if isinstance(job.trigger,
                                                                                         IntervalTrigger) else "date"}
                                                    for job in jobs]}
        return Response(json.dumps(payload, cls=Serialiser), mimetype="application/json")
