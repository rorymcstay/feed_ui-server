from flask_classy import FlaskView
from flask_classy import route
from flask import session, Response
import json

class ActionsStaticData(FlaskView):

    def newActionSchema(self):
        baseActionParams = session["nanny"].get(f'/actionsmanager/newActionSchema/', resp=True)
        return Response(json.dumps(baseActionParams), mimetype='application/json')

    def getActionTypes(self, name):
        ActionTypes= session["nanny"].get(f'/actionsmanager/getActionTypes/{name}', resp=True)
        return Response(json.dumps(ActionTypes), mimetype='application/json')

    def getActionParameters(self, name):
        params = session["nanny"].get(f'/actionsmanager/getActionParameters/{name}', resp=True)
        return Response(json.dumps(params), mimetype='application/json')

    def getPossibleValues(self):
        possible_values = session["nanny"].get(f'/actionsmanager/getPossibleValues/', resp=True)
        return Response(json.dumps(possible_values), mimetype='application/json')


