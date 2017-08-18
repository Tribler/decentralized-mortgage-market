import json
import os

from twisted.web import resource


class EventsEndpoint(resource.Resource):
    """
    This class handles requests for events, which are read from the database.
    """

    def __init__(self, database):
        resource.Resource.__init__(self)
        self.database = database

    def render_GET(self, request):
        """
        Read and return events from the database
        """
        limit = 100
        if 'limit' in request.args:
            limit = int(request.args['q'][0])

        events = [{'timestamp': timestamp, 'level': level, 'message': message} for
                  timestamp, level, message in self.database.get_events(limit=limit)]

        return json.dumps({"events": events})
