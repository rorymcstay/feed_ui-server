import json
from datetime import datetime, timedelta
from typing import List

import sys
import os
from apscheduler.job import Job
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from docker import client as dockerClient
import requests

from feed.settings import kafka_params, mongo_params, nanny_params
from flask import request, Response, session
from flask_classy import FlaskView, route
from kafka import KafkaProducer
from src.main.tables import Serialiser
import logging
from feed.service import Client


class ScheduledActionChain:

    def __init__(self, name, **kwargs):
        self.name = name
        self.trigger = kwargs.get("trigger")
        self.increment = kwargs.get("increment")
        self.increment_size = kwargs.get("increment_size")
        self.time_out = kwargs.get("time_out")


class JobExecutor:
    nanny = Client('nanny', check_health=False, **nanny_params)
    producer = KafkaProducer(**kafka_params, value_serializer=lambda v: json.dumps(v).encode('utf-8'))


    @classmethod
    def publishActionChain(cls, actionChain, queue, userID):
        cls.nanny.behalf = userID
        chainParams = cls.nanny.get(f'/actionsmanager/getActionChain/{actionChain}', resp=True)
        topic = f'{os.getenv("KAFKA_TOPIC_PREFIX", "u")}-{queue}'
        logging.info(f'publishing {actionChain} to {topic}')
        cls.producer.send(topic=topic, value=chainParams, key=bytes(chainParams.get('name'), 'utf-8'))


class ScheduleManager(FlaskView):
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.job_store = MongoDBJobStore(database=os.getenv("CHAIN_DB", 'actionChains'), collection='client_scheduler_jobs', **mongo_params)
        self.scheduler.add_jobstore(self.job_store)
        self.executor = JobExecutor()
        if len(sys.argv) > 1 and sys.argv[1] == '--clear':
            self.scheduler.remove_all_jobs()
        self.scheduler.start()
        """
        If you schedule jobs in a persistent job store during your application’s initialization, you
        MUST define an explicit ID for the job and use replace_existing=True or you will get a new copy
        of the job every time your application restarts!Tip
        """

    @route("scheduleActionChain/<string:queue>/<string:actionChain>", methods=["PUT"])
    def scheduleActionChain(self, queue, actionChain):
        # TODO: Do check on queue here
        logging.info(f'adding job for {actionChain} {request.get_json()}')
        job = ScheduledActionChain(actionChain, **request.get_json())
        if job.increment is '':
            return Response(json.dumps({'valid': False, 'job': job.__dict__, 'reason': "You must specify increment to be one of 'days', 'seconds', or 'hours'"}), status=200, mimetype='application/json')
        timing = {
            job.increment: int(job.increment_size),
        } if job.trigger == 'interval' else {
            "run_date": datetime.now() + timedelta(**{job.increment: int(job.increment_size)})
        }
        try:
            self.scheduler.add_job(self.executor.publishActionChain, job.trigger, name=f'{actionChain}:{session.userID}', args=[actionChain, queue, session.userID], **timing)
        except LookupError as ex:
            return Response(json.dumps({'valid': False, 'reason': f'You must specify a valid trigger. "{job.trigger}" is not.'}), mimetype='application/json')
        return Response(json.dumps({'valid': True, 'message': f'{actionChain}: {datetime.now() + timedelta(**{job.increment: int(job.increment_size)})}'}), mimetype='application/json')

    def getStatus(self):
        isRunning = self.scheduler.running
        jobs: List[Job] = self.scheduler.get_jobs()
        payload = {"isRunning": isRunning, "jobs": [{'job_id': job.id,
                                                     'job_name': job.name,
                                                     'next_run': job.next_run_time,
                                                     'trigger': "interval" if isinstance(job.trigger,
                                                                                         IntervalTrigger) else "date"}
                                                    for job in jobs]}
        return Response(json.dumps(payload, cls=Serialiser), mimetype="application/json")
