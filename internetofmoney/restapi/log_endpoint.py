import json
import os

from twisted.web import resource


class LogEndpoint(resource.Resource):
    """
    This class returns by default the last 100 lines of the log file.
    """

    def __init__(self, cache_dir):
        resource.Resource.__init__(self)
        self.cache_dir = cache_dir

    def render_GET(self, request):
        """
        Read and return the log file
        """
        limit = 100
        if 'limit' in request.args:
            limit = int(request.args['q'][0])

        with open(os.path.join(self.cache_dir, 'iom.log')) as log_file:
            content = log_file.readlines()[-limit:]

        return json.dumps({"log": '\n'.join(content)})
