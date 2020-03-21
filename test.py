
from feed.testutils import TestFactory
from src.main.feedmanager import FeedManager
from unittest import TestCase
import json
testFactory = TestFactory(FeedManager, 3333)

tests = testFactory()


if __name__ == "__main__":
    print(TestCase.countTestCases(tests))
    print(json.dumps(dir(tests), indent=4))

