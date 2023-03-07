"""Base Integration for Cortex XSOAR - Unit Tests file

Pytest Unit Tests: all funcion names must start with "test_"

More details: https://xsoar.pan.dev/docs/integrations/unit-testing

MAKE SURE YOU REVIEW/REPLACE ALL THE COMMENTS MARKED AS "TODO"

You must add at least a Unit Test function for every XSOAR command
you are implementing with your integration
"""

import json
import io
# import demistomock as demisto
# import pytest
# from DatadogCloudSIEM import create_event_command
# from datadog_api_client import ApiClient, Configuration

def util_load_json(path):
    with io.open(path, mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


# TODO: REMOVE the following dummy unit test function
def test_baseintegration_dummy():
    """Tests helloworld-say-hello command function.

    Checks the output of the command function with the expected output.

    No mock is needed here because the say_hello_command does not call
    any external API.
    """
    from BaseIntegration import Client, baseintegration_dummy_command

    client = Client(base_url='some_mock_url', verify=False)
    args = {
        'dummy': 'this is a dummy response'
    }
    response = baseintegration_dummy_command(client, args)

    mock_response = util_load_json('test_data/create-event-response.json')

    assert response.outputs == mock_response
# TODO: ADD HERE unit tests for every command
# CREATE_EVENT_RESPONSE = util_load_json("test_data/create-event-response.json")


# def init_params():
#     return {
#         'app_key': 'WRONG_CLIENT_ID_TEST',
#         'api_key': 'CLIENT_SECRET_TEST',
#     }
#

# def test_test_module_raise_exception(mocker):
#     mocker.patch.object(demisto, 'params', return_value=init_params())
#     mocker.patch('requests.sessions.Session.send', return_value=MockedResponse(400))
#
#     from CybersixgillActionableAlerts import test_module
#
#     with pytest.raises(Exception):
#         test_module()

# @pytest.mark.parametrize('raw_response, expected', [(CREATE_EVENT_RESPONSE, CREATE_EVENT_RESPONSE)])
# def test_create_event_command( raw_response, expected):
#     config = Configuration()
#     args ={
#         "text": "A text",
#         "title": "A title"
#     }
#     create_event_command(config, args)
#     """
#     Tests get_threat_list_command function.
#
#         Given:
#             - mocker object.
#             - raw_response test data.
#             - expected output.
#
#         When:
#             - Running the 'get_threat_list_command'.
#
#         Then:
#             - Checks that the context output and the readable output of the command function are as expected.
#     """
#    mocker.patch.object(client, 'query_cisco_umbrella_api', side_effect=[raw_response] * 5)
    # args = {
    #     "limit": 5,
    #     "from": 1662015255000,
    #     "to": 1662447255000,
    #     "offset": 0
    # }
    # with open(os.path.join('test_data', 'command_readable_output/threat_command_readable_output.md'), 'r') as f:
    #     readable_output = f.read()
    # command_results = get_threat_list_command(client, args)
    #
    # # results is CommandResults list
    # context_detail = command_results.to_context()['Contents']
    # assert context_detail == expected.get("data")
    # assert command_results.readable_output == readable_output
