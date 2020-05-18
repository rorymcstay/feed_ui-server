from unittest import TestCase
import logging
import time
import unittest
import os
import docker

from src.main.tables import TableManager
from feed.testinterfaces import PostgresTestInterface, MongoTestInterface, ServiceFactory


sh = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -%(message)s |%(filename)s:%(lineno)d')

sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
tblLogger = logging.getLogger('src')
tblLogger.addHandler(sh)
tblLogger.setLevel(logging.DEBUG)

NannyMock = ServiceFactory('nanny')

class TestTableManager(NannyMock, PostgresTestInterface, MongoTestInterface):

    @classmethod
    def setUpClass(cls):
        super(PostgresTestInterface, cls).setUpClass()
        super(MongoTestInterface, cls).setUpClass()
        super(NannyMock, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(PostgresTestInterface, cls).tearDownClass()
        super(MongoTestInterface, cls).tearDownClass()
        super(NannyMock, cls).tearDownClass()

    @classmethod
    def setUp(cls):
        cls.tableManager = TableManager()

    @unittest.skip
    def test_getTableNames(self):
        ret = self.tableManager.getTableNames('DoneDealCars')
        tables = ret.json
        self.assertEqual(['t_stg_donedeal_cars_results'], tables)
        ret2 = self.tableManager.getTableNames('NotInTheDataBase')
        tables = ret2.json
        self.assertEqual([], tables)

    @unittest.skip
    def test_getAllColumns(self):
        cols = self.tableManager.getAllColumns('t_stg_donedeal_cars_results').json
        self.assertNotEquals(len(cols), 0)

    @unittest.skip
    def test_getColumnSchema(self):
        colSchema = self.tableManager.getColumnSchema('t_stg_donedeal_cars_results').json
        self.assertNotEquals(len(colSchema), 0)
        [
            self.assertSetEqual(set(['Header', 'accessor']), set(i.keys())) for i in colSchema
        ]

    @unittest.skip
    def test_getMappingValue(self):
        pass


if __name__ == '__main__':
    unittest.main()
