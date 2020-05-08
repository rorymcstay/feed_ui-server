from unittest import TestCase
import logging
import time
import unittest
import os
import docker

from src.main.tables import TableManager


sh = logging.FileHandler('/home/rory/app/feed/tmp/logs/ui-server.tables.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -%(message)s |%(filename)s:%(lineno)d')

sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
tblLogger = logging.getLogger('src')
tblLogger.addHandler(sh)
tblLogger.setLevel(logging.DEBUG)

class TestTableManager(TestCase):

    @classmethod
    def setUp(cls):
        cls.tableManager = TableManager()
    def test_getTableNames(self):
        ret = self.tableManager.getTableNames('DoneDealCars')
        tables = ret.json
        self.assertEqual(['t_stg_donedeal_cars_results'], tables)
        ret2 = self.tableManager.getTableNames('NotInTheDataBase')
        tables = ret2.json
        self.assertEqual([], tables)

    def test_getAllColumns(self):
        cols = self.tableManager.getAllColumns('t_stg_donedeal_cars_results').json
        self.assertNotEquals(len(cols), 0)

    def test_getColumnSchema(self):
        colSchema = self.tableManager.getColumnSchema('t_stg_donedeal_cars_results').json
        self.assertNotEquals(len(colSchema), 0)
        [
            self.assertSetEqual(set(['Header', 'accessor']), set(i.keys())) for i in colSchema
        ]

    def test_getMappingValue(self):
        pass


