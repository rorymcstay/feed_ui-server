import _sre
import json
from unittest import TestCase

from flask import Response
from flask_classy import route

from src.test.testutils import DocumentationTest

@route("...", methods=['GET', 'POST'])
def getFeeds():
    """
    <example1>
        #request: /getFeeds/
        #response: ["donedeal", "pistonheads"]
    <example1/>

    <example2>
        #request: /getFeeds/
        #payload: {"key": "value"}
        #response: ["donedeal", "pistonheads"]
    <example2/>

    :return:
    """
    pass


class TestDocumentationTest(TestCase):
    def test__test_case_regex(self):
        regex = DocumentationTest._testCaseRegex('exampleName')
        # self.assert_(isinstance(regex,  _sre.SRE_Pattern))
        self.assert_(regex.pattern == '<exampleName>|<exampleName/>')

    def test_get_valid_methods(self):
        docTest = DocumentationTest(getFeeds)
        mets = docTest.getValidMethods()
        self.assert_(mets == ['GET', 'POST'])

    def test_get_test_clauses(self):
        docTest = DocumentationTest(getFeeds)
        mets = docTest.getTestClauses('example1')
        self.assert_(mets.get('request') is not None)
        self.assert_(mets.get('response') is not None)
        mets = docTest.getTestClauses('example2')
        self.assert_(mets.get('request') is not None)
        self.assert_(mets.get('response') is not None)
        self.assert_(mets.get('payload') is not None)

    def test_get_names(self):
        docTest = DocumentationTest(getFeeds)
        names = docTest.getNames()
        self.assert_('example1' in names)
        self.assert_('example2' in names)

    def test_generate(self):
        er = DocumentationTest.generate(getFeeds)
        self.assert_(er.cases.get('response') is not None)
        self.assert_(er.cases.get('request') is not None)
