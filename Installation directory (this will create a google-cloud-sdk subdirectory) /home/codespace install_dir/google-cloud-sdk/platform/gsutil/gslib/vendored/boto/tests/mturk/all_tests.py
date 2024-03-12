
import unittest
import doctest
from glob import glob

from .create_hit_test import *
from .create_hit_with_qualifications import *
from .create_hit_external import *
from .create_hit_with_qualifications import *
from .hit_persistence import *

doctest_suite = doctest.DocFileSuite(
	*glob('*.doctest'),
	**{'optionflags': doctest.REPORT_ONLY_FIRST_FAILURE}
	)

class Program(unittest.TestProgram):
	def runTests(self, *args, **kwargs):
		self.test = unittest.TestSuite([self.test, doctest_suite])
		super(Program, self).runTests(*args, **kwargs)

if __name__ == '__main__':
	Program()

