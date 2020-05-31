from flask_classy import FlaskView
from flask_classy import route

class ActionsStaticData(FlaskView):

    def newActionSchema(self):
        baseActionParams = session["nanny"].get('/actionsmanager/newActionSchema/', resp=True)
        return Response(json.dumps(baseActionParams), mimetype='application/json')

    def getActionTypes(self, name):
        ActionTypes= session["nanny"].get('/actionsmanager/getActionTypes/', resp=True)
        return Response(json.dumps(ActionTypes), mimetype='application/json')

    def getActionParameters(self, name):
        params = session["nanny"].get('/actionsmanager/getActionParameters/', resp=True)
        return Response(json.dumps(params), mimetype='application/json')

    def getPossibleValues(self):
        possible_values = session["nanny"].get('/actionsmanager/getPossibleValues/', resp=True)
        return Response(json.dumps(possible_values), mimetype='application/json')


