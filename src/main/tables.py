import json
from datetime import datetime
from json import JSONEncoder

import psycopg2 as psycopg2
from flask import Response, request
from flask_classy import FlaskView, route
from psycopg2._psycopg import connection, cursor
from pymongo import MongoClient

from settings import database_parameters
from settings import mongo_params


class TableManager(FlaskView):
    client: connection = psycopg2.connect(**database_parameters)
    mongo = MongoClient(**mongo_params)
    client.autocommit = True
    numberFields = {}

    def getTableTypes(self):
        return [table.get("name") for table in self.mongo["table"]["type"].find({})]

    def getTableNames(self, feedName):
        query = f"""
        select table_name from information_schema.tables
        where table_name like '%{feedName}%'"""

        c: cursor = self.client.cursor()
        c.execute(query)
        results = [name[0] for name in c.fetchall()]
        return Response(json.dumps(results, cls=Serialiser), mimetype='application/json')

    def getAllColumns(self, tableName):
        query = """
        SELECT column_name
        FROM information_schema.columns
        where table_name = '{}';
        """.format(tableName)
        c: cursor = self.client.cursor()
        c.execute(query)
        results = [name[0] for name in c.fetchall()]
        return Response(json.dumps(results, cls=Serialiser), mimetype='application/json')

    @route('/getResults/<int:page>/<int:pageSize>', methods=['PUT', 'GET'])
    def getResults(self, page, pageSize):
        req = request.get_json()
        query = "select {columns} from {tableName} {predicates} limit {} offset {}".format(page, pageSize, **req)
        c: cursor = self.client.cursor()
        c.execute(f'select count(*) from {req.get("tableName")}')

        pages = c.fetchone()[0]/pageSize
        c.execute(query)
        data = list(map(lambda row: {c.description[i].name: row[i] for i in range(len(c.description))}, c.fetchall()))
        columns = [{"Header": column.name, "accessor": column.name} for column in c.description]
        response = {"data": data, "columns": columns, "pages": pages}
        return Response(json.dumps(response, cls=Serialiser))

    def getMappingSchema(self):
        form = self.mongo['mapping']['forms'].find_one({"type": "simple_mapping"})
        return Response(json.dumps(form), mimetype='application/json')

    def getMappingValue(self, name):
        val = self.mongo['mapping']['values'].find_one({"name": name})
        if val is not None:
            val = val.get('value')
        return Response(json.dumps(val, cls=Serialiser), mimetype='application/json')

    @route('/uploadMapping/<string:name>', methods=['PUT'])
    def uploadMapping(self, name):
        val = request.get_json()
        tableName = val.pop("tableName")
        obj = {"name": name, "value": val, "tableName": tableName}
        self.mongo['mapping']['values'].replace_one({"name": name}, obj, upsert=True)
        return "ok"


class Serialiser(JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime):
            return str(o).split('.')[0]


