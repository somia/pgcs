import sys
import threading
import traceback

class FutureError(Exception):
	def __init__(self, exception):
		Exception.__init__(self)
		self.exception = exception

class Future(object):
	def __init__(self, call, *args):
		self._thread = threading.Thread(target=self._run, args=(call, args))
		self._thread.daemon = True
		self._thread.start()

	def _run(self, call, args):
		try:
			self._result = call(*args)
			self._error = None
		except:
			exctype, self._error, trace = sys.exc_info()
			traceback.print_exception(exctype, self._error, trace)

	def get(self):
		self._thread.join()
		if self._error is not None:
			raise FutureError(self._error)
		return self._result
