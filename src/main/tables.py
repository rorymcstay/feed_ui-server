import json
from datetime import datetime
from json import JSONEncoder

import psycopg2 as psycopg2
from flask import Response, request
from flask_classy import FlaskView, route
from psycopg2._psycopg import connection, cursor
from pymongo import MongoClient
import requests
from feed.settings import database_parameters
from feed.settings import mongo_params, nanny_params

import logging as logger

logging = logger.getLogger(__name__)


class TableManager(FlaskView):
    client: connection = psycopg2.connect(**database_parameters)
    mongo = MongoClient(**mongo_params)
    client.autocommit = True
    numberFields = {}

    def _getTableTypes(self):
        return [table.get("name") for table in self.mongo["table"]["type"].find({})]

    def getTableNames(self, feedName):
        actions = requests.get("http://{host}:{port}/actionsmanager/queryActionChain/{name}/actions".format(name=feedName, **nanny_params))
        try:
            actions = actions.json()
            actions = actions.get('actions', [])
        except:
            logging.info(f'actionchain not found for feedName=[{feedName}]. response was data=[{actions.data}], status=[{actions.status}]')
        if actions is None:
            actions = []
        captureActions = filter(lambda action: action.get('actionType') == 'CaptureAction', actions)
        if not captureActions:
            captureActions = []
        captures = list(map(lambda action: "table_name like '%{}%'".format(action.get('captureName', None)), captureActions))
        if len (captures) == 0:
            captures.append("table_name like '%{}%'".format(feedName))
        query = f"""
        select table_name from information_schema.tables
        where {" or ".join(captures)}"""

        c: cursor = self.client.cursor()
        c.execute(query)
        results = [name[0] for name in c.fetchall()]
        logging.info(f'returning {len(results)} tablenames for {feedName}')
        return Response(json.dumps(results, cls=Serialiser), mimetype='application/json')

    def getAllColumns(self, tableName):
        query = f"""
        SELECT column_name
        FROM information_schema.columns
        where table_name = '{tableName}';
        """
        c: cursor = self.client.cursor()
        c.execute(query)
        results = [name[0] for name in c.fetchall()]
        return Response(json.dumps(results, cls=Serialiser), mimetype='application/json')

    def _getColumnNames(self, tableName):
        query = """
                SELECT column_name
                FROM information_schema.columns
                where table_name = '{}';
                """.format(tableName)
        c: cursor = self.client.cursor()
        c.execute(query)
        results = [name[0] for name in c.fetchall()]
        logging.debug(f'have column names: {results}')
        return results

    def getColumnSchema(self, tableName):
        results = self._getColumnNames(tableName)
        columns = [{"Header": column, "accessor": column} for column in results]
        logging.debug(f'have column schema of length {len(columns)}')
        return Response(json.dumps(columns, cls=Serialiser), mimetype='application/json')

    def _checkTableStatus(self, name):
        query = f"""
        SELECT datname, pid, state, query, age(clock_timestamp(), query_start) AS age
        FROM pg_stat_activity
        WHERE state <> 'idle'
            AND query NOT LIKE '% FROM pg_stat_activity %' and query like '%{name}%'
        ORDER By age;
        """
        c = self.client.cursor()
        c.execute(query)
        logging.debug(f'executing {query}')
        data = list(map(lambda row: {c.description[i].name: row[i] for i in range(len(c.description))}, c.fetchall()))
        if len(data) == 0:
            logging.info(f'table {name} is FREE')
            return True
        else:
            logging.info(f'table {name} is BUSY')
            return False

    def _getTableCount(self, tableName):
        countQ = f'select count(*) from {tableName}'
        logging.debug(f'executing: {countQ}')
        c = self.client.cursor()
        c.execute(countQ)
        count = c.fetchone()[0]
        return count

    @route('/getResults/<int:page>/<int:pageSize>', methods=['POST', 'GET'])
    def getResults(self, page, pageSize):
        req = request.get_json()
        tableName = req.get("tableName")
        query = "select {columns} from {tableName} {predicates} limit {size} offset {page}".format(size=pageSize, page=page, **req)
        c: cursor = self.client.cursor()
        if not self._checkTableStatus(tableName):
            columns = self._getColumnNames(tableName)
            data = {col: "loading" for col in columns}
            payload = {"data": data, "pages": 101}
            return Response(json.dumps([payload]), mimetype='application/json')
        count = self._getTableCount(tableName)
        pages = round(count/pageSize)
        logging.debug(f'executing {query}')
        c.execute(query)
        data = list(map(lambda row: {c.description[i].name: row[i] for i in range(len(c.description))}, c.fetchall()))
        #columns = [{"Header": column.name, "accessor": column.name} for column in c.description]
        logging.info(f'returning {len(data)}/{count} results for {tableName}')
        response = {"data": data, "pages": pages}
        return Response(json.dumps(response, cls=Serialiser))

    def getMappingSchema(self):
        form = self.mongo['mapping']['forms'].find_one({"type": "simple_mapping"})
        return Response(json.dumps(form), mimetype='application/json')

    def getMappingValue(self, mapType, name):
        """
        return the mapping to caller

        :param: mapType one of 'list' or 'map'
        :param: name, name of the feed
        """

        val = self.mongo['mapping']['values'].find_one({"name": name})
        if val is not None:
            logging.debug(f'Have mapping for {name}')
            val = val.get('value')
        else:
            logging.debug(f'No mapping for {name}')
            val = {"mapping": []}
        return Response(json.dumps(val.get('mapping') if mapType == "list" else self._to_key_vals(val.get('mapping'))
                                   , cls=Serialiser)
                        , mimetype='application/json')

    def _make_mapping(self, key_val_map):
        """
        convert map type mapping to list type mapping
        """
        return [{"staging_column_name": key, "final_column_name": key_val_map[key]}
                for key in filter(lambda k: len(key_val_map[k]) != 0, key_val_map)]

    def _to_key_vals(self, mapping):
        """
        conver list type mapping to map type.
        """
        return {col.get("staging_column_name"): col.get("final_column_name") for col in mapping}

    @route('/uploadMapping/<string:name>', methods=['PUT'])
    def uploadMapping(self, name):
        """
        send: {"tableName": name, "mapping": `mapping`

        upload mapping of the form:

            [
                {"staging_column_name": "name", "final_column_name": "newName"},...
            ]

        or:

            {"staging_column_name": "final_column_name",...}

        """
        val = request.get_json()
        tableName = val.pop("tableName")
        if not isinstance(val.get("mapping"), list):
            logging.info(f'uploading a map type mapping')
            val["mapping"] = self._make_mapping(val.get("mapping"))

        obj = {"name": name, "value": val, "tableName": tableName}
        logging.info(f'inserting mapping {obj} for {name}')
        self.mongo['mapping']['values'].replace_one({"name": name}, obj, upsert=True)
        return "ok"


class Serialiser(JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime):
            return str(o).split('.')[0]
