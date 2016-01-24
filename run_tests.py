#!/usr/bin/env python
from unittest import TestLoader, TextTestRunner

loader = TestLoader()
testRunner = TextTestRunner()
modelsTestSuite = loader.discover('.', pattern='test_models.py')
APITestSuite = loader.discover('.', pattern='test_api_server.py')
print('\n\tRUNNING MODEL TEST CASES\n')
testRunner.run(modelsTestSuite)
print('\n\tRUNNING API TEST CASES\n')
testRunner.run(APITestSuite)
