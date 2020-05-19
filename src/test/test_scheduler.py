from feed.testinterfaces import MongoTestInterface, KafkaTestInterface
import logging
import time
import unittest
import os
import docker
from feed.actionchains import ActionChain

from src.main.scheduler import ScheduleManager


sh = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -%(message)s |%(filename)s:%(lineno)d')

sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
tblLogger = logging.getLogger('src')
tblLogger.addHandler(sh)
tblLogger.setLevel(logging.DEBUG)


class TestSchedulerManager(MongoTestInterface, KafkaTestInterface):

    @classmethod
    def setUpClass(cls):
        super(KafkaTestInterface, cls).setUpClass()
        super(MongoTestInterface, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(KafkaTestInterface, cls).tearDownClass(cls)
        super(MongoTestInterface, cls).tearDownClass(cls)

    def setUp(cls):
        cls.scheduleManager = ScheduleManager()

    def test_scheduleActionChain(self):
        self.scheduleManager.scheduleActionChain('worker-queue', ActionChain(name='DoneDeal', actions=[], startUrl='test'))

    # TODO need to mock requests object
    #def test_scheduleActionChain(ScheduleManager):
    #    cls.scheduleManager.scheduleActionChain('leader-route',
if __name__ == '__main__':
    unittest.main()
