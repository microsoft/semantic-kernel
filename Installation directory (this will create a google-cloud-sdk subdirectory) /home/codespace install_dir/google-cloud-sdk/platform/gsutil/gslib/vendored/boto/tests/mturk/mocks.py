from boto.mturk.connection import MTurkConnection as RealMTurkConnection

class MTurkConnection(RealMTurkConnection):
	"""
	Mock MTurkConnection that doesn't connect, but instead just prepares
	the request and captures information about its usage.
	"""
	
	def _process_request(self, *args, **kwargs):
		saved_args = self.__dict__.setdefault('_mock_saved_args', dict())
		saved_args['_process_request'] = (args, kwargs)
