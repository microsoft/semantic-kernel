from __future__ import absolute_import
from boto.mturk.test.support import unittest

sel_args = ('localhost', 4444, '*chrome', 'https://workersandbox.mturk.com')

class SeleniumFailed(object):
	def __init__(self, message):
		self.message = message
	def __nonzero__(self):
		return False

def has_selenium():
	try:
		from selenium import selenium
		globals().update(selenium=selenium)
		sel = selenium(*sel_args)
		# a little trick to see if the server is responding
		try:
			sel.do_command('shutdown', '')
		except Exception as e:
			if not 'Server Exception' in str(e):
				raise
		result = True
	except ImportError:
		result = SeleniumFailed('selenium RC not installed')
	except Exception:
		msg = 'Error occurred initializing selenium: %s' % e
		result = SeleniumFailed(msg)

	# overwrite has_selenium, so the same result is returned every time
	globals().update(has_selenium=lambda: result)
	return result

identity = lambda x: x

def skip_unless_has_selenium():
	res = has_selenium()
	if not res:
		return unittest.skip(res.message)
	return identity

def complete_hit(hit_type_id, response='Some Response'):
	verificationErrors = []
	sel = selenium(*sel_args)
	sel.start()
	sel.open("/mturk/welcome")
	sel.click("lnkWorkerSignin")
	sel.wait_for_page_to_load("30000")
	sel.type("email", "boto.tester@example.com")
	sel.type("password", "BotoTest")
	sel.click("Continue")
	sel.wait_for_page_to_load("30000")
	sel.open("/mturk/preview?groupId={hit_type_id}".format(**vars()))
	sel.click("/accept")
	sel.wait_for_page_to_load("30000")
	sel.type("Answer_1_FreeText", response)
	sel.click("//div[5]/table/tbody/tr[2]/td[1]/input")
	sel.wait_for_page_to_load("30000")
	sel.click("link=Sign Out")
	sel.wait_for_page_to_load("30000")
	sel.stop()
