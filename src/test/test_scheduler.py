from feed.testinterfaces import MongoTestInterface
import logging
import time
import unittest
import os
import docker

from src.main.scheduler import ScheduleManager


sh = logging.FileHandler('/home/rory/app/feed/tmp/logs/ui-server.tables.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -%(message)s |%(filename)s:%(lineno)d')

sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
tblLogger = logging.getLogger('src')
tblLogger.addHandler(sh)
tblLogger.setLevel(logging.DEBUG)

class TestSchedulerManager(MongoTestInterface):
    def setUp(cls):
        cls.scheduleManager = ScheduleManager()
    # TODO need to mock requests object
    #def test_scheduleActionChain(ScheduleManager):
    #    cls.scheduleManager.scheduleActionChain('leader-route',
