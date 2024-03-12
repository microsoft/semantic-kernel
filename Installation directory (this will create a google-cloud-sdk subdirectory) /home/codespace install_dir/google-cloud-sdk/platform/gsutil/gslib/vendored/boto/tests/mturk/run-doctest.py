import argparse
import doctest

parser = argparse.ArgumentParser(
	description="Run a test by name"
	)
parser.add_argument('test_name')
args = parser.parse_args()

doctest.testfile(
	args.test_name,
	optionflags=doctest.REPORT_ONLY_FIRST_FAILURE
	)
