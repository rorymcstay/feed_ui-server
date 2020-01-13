import json
import logging
import re
from inspect import signature, getfullargspec
from json import JSONDecodeError
from typing import Union
from flask import Flask, Response, request
from flask_classy import FlaskView

NOT_IMPLEMENTED=509
WRONG_NUMBER_ARGS=510

class ExpectedRequest:

    def __init__(self, reqString=None, resString=None, payload=None,mimetype=None):
        if reqString == None:
            assert(False and f'{reqString} not Implemented')
        if payload is not None:
            reqpayload = request.json()
            logging.info(f'received payload to endpoint {reqString}: {json.dumps(reqpayload)}')
            assert(request.json().keys() == payload.keys() and
                   f'''body of request to {resString} was malformed.
                        actual:{json.dumps(request.json())}
                        expected: {json.dumps(payload)}''')

        items = reqString.split(" ")
        self.method = items[0]
        self.route =items[1]
        self.payload = payload
        mimetype = mimetype
        self.response = Response(resString, status=200, mimetype=mimetype)

class FailResponse(Response):

    def __init__(self):
        super().__init__('case not found', status=404)


def testCaseGenerator(func: callable):
    regex = re.compile('(@.*: *\n|:param|:return|""")')
    casesregex = re.compile('(#request:|#response:|#payload:)')
    nameregex = re.compile('@.*:')
    doc = func.__doc__
    for chunk in regex.findall(doc):
        name = nameregex.match(chunk)
        name = name[1:-1] if '@' in name else None
        cases = casesregex.findall(chunk)
        if cases is not None and name is not None:
            if len(cases) > 3:
                assert(False and f'invalid documentation of {func} for test case {name}')
            elif len(cases) == 2:
                payload = None
            elif len(cases) == 1:
                assert(False and f'testcase of {func} for test case {name} is not valid. Missing response or request item in documentation')
            else:
                try:
                    payload = json.loads(cases[2])
                except JSONDecodeError as e:
                    assert(False and
                           f'payload of {func} for test case {name} is not valid. JSONDecodeError postion: {e.pos} line: {e.lineno} col: {e.colno} message: {e.msg}')
            items = casesregex.split(chunk)
            req = items[1]
            res = items[0]
            type = 'text' if all(c not in res for c in '"{}:') else 'json'
            if type == 'json':
                try:
                    json.loads(res)
                except JSONDecodeError as e:
                    assert(False and
                           f'response of {func} for test case {name} is not valid. JSONDecodeError postion: {e.pos} line: {e.lineno} col: {e.colno} message: {e.msg}')
            yield ExpectedRequest(req, res, payload, f'application/{type}')



def MockFactory(service, app):

    class MockService(service):

        def __init__(self, app):
            self.app = app
            self.cases = {}

        def register(self):
            serviceMethods = [method for method in dir(service) if callable(
                getattr(service, method)) if not '_' in method]
            self.actions = {}
            for method in serviceMethods:
                siglen = len(signature(getattr(service, method)))
                args = getfullargspec(getattr(service, method))
                reqString = lambda *args: f'{service.get_route_base()}/{method}/{"/".join(args)}'
                action = lambda *args: self.cases.get(reqString) if len(args) == siglen else FailResponse()
                self.actions.update({method: action})
                self.mockMethod(method)
                params = "/".join([f'<{pname}>' for pname in args[0][1:]])
                self.app.add_url_rule(f'{service.get_route_base()}/{method}/{params}', method, self.actions.get(method))

        def mockMethod(self, methodName: str):
            self.cases.update((case.route, case for case in testCaseGenerator(getattr(service, methodName))))

        @staticmethod
        def _modifyResponse(res: Response, body, status):
            if res.status == NOT_IMPLEMENTED:
                return
            type = 'text' if isinstance(body, str) else 'json'
            # wrong number of arguments passed in url
            assert(res.status != WRONG_NUMBER_ARGS)
            res.mimetype = f'application/{type}'
            res.data = body
            res.status = status
            return res

if __name__ == '__main__':
    from src.test