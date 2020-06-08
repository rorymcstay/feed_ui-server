from flask.sessions import SessionMixin
from flask import session
import time
import logging


class User(dict, SessionMixin):

    def __init__(self, **kwargs):
        self.firstName = kwargs.get('firstName', None)
        self.lastName = kwargs.get('secondName', None)
        self.email = kwargs.get('email', None)
        self.userID = str(kwargs.get('userID', None))
        self.lastActive = time.time()
        self.name = kwargs.get('name', None) #  Chain name - session objects must be linked to a chain name
        self.modified = True

    def __dict__(self):
        return dict(
                firstName=self.firstName,
                lastName=self.lastName,
                email=self.email,
                userID=self.userID,
                lastActive=self.lastActive,
                lastChain=self.name
                )

    def example_sources(self, position, name):
        # TODO this should be improved further to get that item of the list
        logging.debug(f'looking for sample_page with name={name} and userID=session.userID')
        sample = session['chain_db']['sample_pages'].find_one({'name': name, 'position': int(position), 'userID': session.userID})
        self.modified=False
        if sample is None:
            return None
        else:
            return sample.get('source', '<html><body><div></div></body></html>')

    def setEmail(self, email):
        self.modified = True
        self.email = email

