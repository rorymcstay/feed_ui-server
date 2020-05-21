from feed.testinterfaces import MongoTestInterface, KafkaTestInterface, PostgresTestInterface
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


class TestSchedulerManager(MongoTestInterface, KafkaTestInterface, PostgresTestInterface):

    @classmethod
    def setUpClass(cls):
        os.environ['KAFKA_ADDRESS'] = 'test_kafka:29092'
        MongoTestInterface.createMongo()
        KafkaTestInterface.createKafka()
        PostgresTestInterface.createPostgres()


        time.sleep(10)

    @classmethod
    def tearDownClass(cls):
        KafkaTestInterface.killKafka()
        MongoTestInterface.killMongo()
        PostgresTestInterface.killPostgres()

    def setUp(cls):
        print('setting up class')
        from src.main.app import app
        cls.app = app
        cls.scheduleManager = ScheduleManager()

    def test_scheduleActionChain(self):
        example_request = dict(url='test', trigger='interval', increment='days', increment_size=5, time_out=1) # increment_size and increment are unclear
        with self.app.test_request_context(json=example_request):
            self.scheduleManager.scheduleActionChain('worker-queue', 'test')


    # TODO need to mock requests object
    #def test_scheduleActionChain(ScheduleManager):
    #    cls.scheduleManager.scheduleActionChain('leader-route',
if __name__ == '__main__':
    unittest.main()
