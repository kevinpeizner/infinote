#!/usr/bin/env python
from unittest import TestLoader, TextTestRunner

loader = TestLoader()
testSuite = loader.discover('.')
testRunner = TextTestRunner()
testRunner.run(testSuite)
