# Copyright (c) 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import uuid
import websocket
import json
import ddt

from zaqar.tests.unit.transport.websocket import base


@ddt.ddt
class QueueLifecycleBaseTest(base.V1_1Base):

    config_file = "/home/vkmc/zaqar-websocket/tests/etc/websocket_mongodb.conf"

    def setUp(self):
        super(QueueLifecycleBaseTest, self).setUp()

        # NOTE(vkmc): Retrieve the host and port from the config
        self.ws = websocket.WebSocket()
        self.ws.connect("ws://127.0.0.1:9000")

        self.headers = {
            'Client-ID': str(uuid.uuid4()),
            'X-Project-ID': '3387309841abc_'
        }

    @staticmethod
    def _create_request(action, body, headers):
        return json.dumps({"action": action,
                           "body": body, "headers": headers})

    def test_empty_project_id(self):
        action = "create_queue"
        body = {"queue_name":"myqueue",
                "metadata": {
                    "key": {
                        "key2": "value",
                        "key3": [1, 2, 3, 4, 5]}
                    }
                }
        headers = {'Client-ID': str(uuid.uuid4())}
        req = self._create_request(action, body, headers)
        self.ws.send(req)

        resp = self.ws.recv()
        print resp
        resp = json.loads(resp)
        print resp

        #assert resp['header']['status'] == 400

    def test_basics_thoroughly(self):
        pass

    def test_name_restrictions(self):
        pass

    def test_project_id_restriction(self):
        pass

    def test_non_ascii_name(self):
        pass

    def test_no_metadata(self):
        pass

    def test_bad_metadata(self):
        pass

    def test_too_much_metadata(self):
        pass

    def test_way_too_much_metadata(self):
        pass

    def test_custom_metadata(self):
        pass

    def test_update_metadata(self):
        pass

    def test_list(self):
        pass