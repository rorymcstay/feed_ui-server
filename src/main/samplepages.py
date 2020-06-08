from flask_classy import FlaskView, route
import os
from bs4 import BeautifulSoup
from flask import session, Response, request
import json
import requests as r
import logging

class HtmlSource:
    def __init__(self, source):
        self.soup = BeautifulSoup(source)
        self._insertSelector()

    def _get_tag(self, tag_type, resource):
        att = {}
        if tag_type == 'link':
            att.update({'rel': "stylesheet"})
            att.update({'href': resource })
        elif tag_type == 'script':
            att.update({'src':resource})
        return self.soup.new_tag(tag_type, **att)

    def _insertSelector(self):
        gadget = self._get_tag('script', '/samplepages/getSelectorGadget/')
        css = self._get_tag('link', '/samplepages/getSelectorGadgetCss/')
        initialise = self._get_tag('script', '/samplepages/getSelectorGadgetInitialise/')
        button = self.soup.new_tag('input', **dict(type="button", id="sg_toggle_btn", value="Toggle SelectorGadget"))
        self.soup.head.append(gadget)
        logging.info(f'added {gadget} to html')
        self.soup.head.append(css)
        self.soup.body.append(initialise)
        logging.info(f'added {css} to html')
        self.soup.body.append(button)
        logging.info(f'added {button} to html')

class SamplePages(FlaskView):

    @route('getSamplePage/<string:name>/<int:position>')
    def getSamplePage(self, name, position):
        num_examples = session["chain_db"]["sample_pages"].count_documents({'userID': session.userID, 'name': name})
        if num_examples <= position:
            logging.info(f'Position {position} not ready yet returning, using {num_examples} instead')
            position = num_examples
        else:
            src = session.example_sources(position, name)
            if not src:
                logging.info(f'Source was None for position={position}, userID={session.userID}, name={name}')
                return Response("<div>RefreshSources</div>", status=200, mimetype='text/html')
            logging.info(f'sending sample source to client, name={name}, sample_source_len={len(src)}')
            enrichedHtmlFile = HtmlSource(src)
            return Response(str(enrichedHtmlFile.soup), status=200, mimetype='text/html')

    def getSourceStatus(self, name):
        # TODO change chain_db to be of class type, so that we can have easier controle over this interface. session['chain_db'].get_collection('...')
        logging.debug(f'counting documents for userID={session.userID}, name={name}')
        num_examples = session["chain_db"]["sample_pages"].count_documents({'userID': session.userID, 'name': name})
        actions = session["nanny"].get(f'/actionsmanager/queryActionChain/{name}/actions', resp=True, error={"actions":[1]})
        logging.info(f'Getting sample page status for {len(actions.get("actions"))} actions, num_examples=[{num_examples}]')
        status =[]
        for i in range(len(actions.get("actions") if isinstance(actions.get("actions"), list) else [1])):
            if i < num_examples:
                status.append({'ready': True})
            else:
                status.append({'ready': False})
        return Response(json.dumps(status), mimetype='application/json')

    def _getSelectorComponent(self, filename):
        with open(f'{os.getenv("SELECTOR_GADGET", "./selector")}/{filename}') as jsfile:
            fileTxt = jsfile.read()
        return Response(fileTxt, status=200, mimetype=f'text/{filename.split(".")[-1]}')

    def getSelectorGadget(self):
        return self._getSelectorComponent('selectorgadget_combined.js')

    def getSelectorGadgetCss(self):
        return self._getSelectorComponent('selectorgadget_combined.css')

    def getSelectorGadgetInitialise(self):
        return self._getSelectorComponent('initialise_gadget.js')


