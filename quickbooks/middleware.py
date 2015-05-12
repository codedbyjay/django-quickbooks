from quickbooks.models import ResponseError


class LogRequestErrors(object):

	def process_response(self, request, response):
		ResponseError.log_error(request, response)
