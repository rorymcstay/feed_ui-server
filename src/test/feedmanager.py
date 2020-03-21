from feed.testutils import TestFactory
from src.main.feedmanager import FeedManager

tests = TestFactory(FeedManager, 3333)


if __name__ == "__main__":
    print(tests.countTestCases())


