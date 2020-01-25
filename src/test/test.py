from feed.testutils import MockFactory
from flask import Flask

from src.main.feedmanager import FeedManager

app = Flask(__name__)

t = MockFactory(FeedManager, app)


if __name__ == '__main__':
    t.init()
    print(app.url_map)
    t.app.run()
