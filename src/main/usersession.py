from flask.sessions import SessionMixin




class User(dict, SessionMixin):

    def __init__(self, **kwargs):
        self.firstName = kwargs.get('firstName', None)
        self.lastName = kwargs.get('secondName', None)
        self.email = kwargs.get('email', None)
        self.userID = kwargs.get('userID', None)
        self.name = kwargs.get('name', None) #  Chain name - session objects must be linked to a chain name

    def __dict__(self):
        return dict(
                firstName=self.firstName,
                lastName=self.lastName,
                email=self.email,
                userID=self.userID
                )

    def setEmail(self, email):
        self.modified = False
        self.email = email

