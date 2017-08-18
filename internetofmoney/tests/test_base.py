import inspect
import os
import shutil
import unittest

import functools
from tempfile import mkdtemp

from internetofmoney.tests.util.exc_util import process_unhandled_exceptions, process_unhandled_twisted_exceptions


class BaseTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)

        def wrap(fun):
            @functools.wraps(fun)
            def check(*argv, **kwargs):
                try:
                    result = fun(*argv, **kwargs)
                except:
                    raise
                else:
                    process_unhandled_exceptions()
                return result
            return check

        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("test_"):
                setattr(self, name, wrap(method))

    def setUp(self):
        self.temp_dir = mkdtemp(suffix="_iom_test")

    def tearDown(self):
        shutil.rmtree(unicode(self.temp_dir), ignore_errors=True)
        process_unhandled_exceptions()
        process_unhandled_twisted_exceptions()
