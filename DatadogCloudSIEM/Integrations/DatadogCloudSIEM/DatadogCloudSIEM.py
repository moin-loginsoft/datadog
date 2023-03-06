"""Base Integration for Cortex XSOAR (aka Demisto)

This is an empty Integration with some basic structure according
to the code conventions.

MAKE SURE YOU REVIEW/REPLACE ALL THE COMMENTS MARKED AS "TODO"

Developer Documentation: https://xsoar.pan.dev/docs/welcome
Code Conventions: https://xsoar.pan.dev/docs/integrations/code-conventions
Linting: https://xsoar.pan.dev/docs/integrations/linting

This is an empty structure file. Check an example at;
https://github.com/demisto/content/blob/master/Packs/HelloWorld/Integrations/HelloWorld/HelloWorld.py

"""

import demistomock as demisto
from CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from CommonServerUserPython import *  # noqa

import urllib3
from typing import Dict, Any

from os import environ
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.authentication_api import AuthenticationApi
from datadog_api_client.v1.api.events_api import EventsApi
from datadog_api_client.v1.model.event_create_request import EventCreateRequest
from datadog_api_client.v1.model.event_priority import EventPriority
from datadog_api_client.v1.model.event_alert_type import EventAlertType
from datetime import datetime
from dateutil.relativedelta import relativedelta
from math import floor


# Disable insecure warnings
urllib3.disable_warnings()

""" CONSTANTS """

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # ISO8601 format with UTC, default in XSOAR
DEFAULT_OFFSET = 0
DEFAULT_PAGE_SIZE = 50
PAGE_NUMBER_ERROR_MSG = "Invalid Input Error: page number should be greater than zero."
PAGE_SIZE_ERROR_MSG = "Invalid Input Error: page size should be greater than zero."
DEFAULT_FROM_DATE = "-7days"
DEFAULT_TO_DATE = "now"
INTEGRATION_CONTEXT_NAME = 'Datadog'

""" HELPER FUNCTIONS """


def date_string_to_timestamp(date: str) -> int:
    return int(
        datetime.strptime(date, DATE_FORMAT).timestamp()
    )


def str_to_bool(s):
    """
    Convert a string representation of a boolean value to a Python boolean value.
    'True', 'true', 'Yes', 'yes', and '1' are considered True.
    'False', 'false', 'No', 'no', and '0' are considered False.
    """
    if s.lower() in ('true', 'yes', '1'):
        return True
    elif s.lower() in ('false', 'no', '0'):
        return False
    else:
        raise ValueError("Invalid string value for boolean conversion: " + s)


def get_command_title_string(sub_context: str, page: Optional[int],
                             page_size: Optional[int]) -> str:
    """
    Define command title
    Args:
        sub_context: Commands sub_context
        page: page_number
        page_size: page_size
    Returns:
        Returns the title for the readable output
    """
    if page and page_size and (page > 0 and page_size > 0):
        return f'{sub_context} List\nCurrent page size: {page_size}\n' \
               f'Showing page {page} out of others that may exist'

    return f"{sub_context} List"


def is_within_18_hours(timestamp):
    # Calculate the current time
    current_time = datetime.now()

    # Convert the given timestamp to datetime object
    timestamp_time = datetime.fromtimestamp(timestamp)

    # Calculate the time difference between current time and timestamp
    time_diff = current_time - timestamp_time

    # Calculate the time difference in hours
    time_diff_hours = time_diff.total_seconds() / 3600

    # Check if the time difference is less than 18 hours
    if time_diff_hours <= 18:
        return True
    else:
        return False


def lookup_to_markdown(results: List[Dict], title: str) -> str:
    headers = results[0] if results else {}
    headers = list(headers.keys())
    markdown = tableToMarkdown(title, results, headers=headers, removeNull=True)
    return markdown

def event_for_lookup(event: Dict) -> Dict:
    event_dict = {
        "Title": event.get("title"),
        "Text": event.get("text"),
        "Date Happened": datetime.fromtimestamp(
            event.get("date_happened", 0)
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "Id": event.get("id"),
        "Priority": event.get("priority"),
        "Source": event.get("source"),
        "Tags": ",".join(tag for tag in event.get("tags", [])),
        "Is Aggregate": event.get('is_aggregate'),
        'Host': event.get('host'),
        'Device Name': event.get('device_name'),
        'Alert Type': event.get('alert_type'),
    }
    return  event_dict


def pagination(limit: Optional[int], page: Optional[int], page_size: Optional[int]):
    """
    Define pagination.
    Args:
        page: The page number.
        page_size: The number of requested results per page.
    Returns:
        limit (int): Records per page.
        offset (int): The number of records to be skipped.
    """
    if page is None:
        page = DEFAULT_OFFSET
    elif page <= 0:
        raise DemistoException(PAGE_NUMBER_ERROR_MSG)
    else:
        page = page - 1

    if page_size is None:
        page_size = DEFAULT_PAGE_SIZE
    elif page_size <= 0:
        raise DemistoException(PAGE_SIZE_ERROR_MSG)

    if limit:
        limit = limit
    elif page_size:
        limit = page_size
    else:
        limit = DEFAULT_PAGE_SIZE
    offset = page * page_size

    return limit, offset


# TODO: ADD HERE ANY HELPER FUNCTION YOU MIGHT NEED (if any)

""" COMMAND FUNCTIONS """


def test_module(configuration) -> str:
    """Tests API connectivity and authentication'

    Returning 'ok' indicates that the integration works like it is supposed to.
    Connection to the service is successful.
    Raises exceptions if something goes wrong.

    :type client: ``Client``
    :param Client: client to use

    :return: 'ok' if test passed, anything else will fail the test.
    :rtype: ``str``
    """

    message: str = ""
    try:
        with ApiClient(configuration) as api_client:
            api_instance = AuthenticationApi(api_client)
            api_instance.validate()
            message = "ok"
    except Exception as e:
        message = "Authorization Error: make sure API Key, Application Key, Site URL is correctly set"
    return message




def create_event_command(configuration, args):
    priority = args.get('priority')
    alert_type = args.get("alert_type")
    if priority and priority not in EventPriority.allowed_values:
        return DemistoException("Priority not in allowed values.")
    if alert_type and alert_type not in EventAlertType.allowed_values:
        return DemistoException("Alert type not in allowed values.")
    date_happened = args.get("date_happened")
    if date_happened:
        date_happened_timestamp = date_string_to_timestamp(date_happened)
        if not is_within_18_hours(date_happened_timestamp):
            readable_output = "The time of the event shall not be older than 18 hours!\n"
            return CommandResults(readable_output=readable_output)

    data = {
        "title": args.get("title"),
        "text": args.get("text"),
        "tags": args.get("tags").split(",") if args.get("tags") else None,
        "alert_type": EventAlertType(args.get("alert_type")),
        "priority": EventPriority(args.get('priority')),
        "aggregation_key": args.get("aggregation_key"),
        "related_event_id": int(args.get("related_event_id")) if args.get("related_event_id") else None,
        "host": args.get("host_name"),
        "device_name": args.get("device_name"),
        "date_happened": date_string_to_timestamp(date_happened) if date_happened else None,
        "source_type_name": args.get("source_type_name"),
    }
    data = {key: value for key, value in data.items() if value is not None}
    body = EventCreateRequest(**data)

    with ApiClient(configuration) as api_client:
        api_instance = EventsApi(api_client)
        response = api_instance.create_event(body=body)
        if response and response.status == "ok":
            readable_output = "Event created successfully!"
        else:
            readable_output = "Something went wrong!"

        return CommandResults(readable_output=readable_output)


def get_events_command(configuration, args):
    with ApiClient(configuration) as api_client:
        api_instance = EventsApi(api_client)

        if args.get("event_id"):
            response = api_instance.get_event(
                event_id=arg_to_number(args.get("event_id"), arg_name="event_id"),
            )
            data = response.get("event", {})
            if data:
                data = data.to_dict()
                event_dict = event_for_lookup(data)
                results = [event_dict]
                title = "Event Details"
                readable_output = lookup_to_markdown(results, title)
            else:
                readable_output = "No event to present.\n"

        else:
            start_time = date_string_to_timestamp(args.get("start_date", (datetime.now() + timedelta(days=-7)).date().strftime(DATE_FORMAT)))
            end_time = date_string_to_timestamp(args.get("end_date", datetime.now().strftime(DATE_FORMAT)))
            page = arg_to_number(args.get("page"), arg_name="page")
            page_size = arg_to_number(args.get("page_size"), arg_name="page_size")
            limit = arg_to_number(args.get("limit"), arg_name="limit")
            limit, offset = pagination(limit, page, page_size)
            datadog_page = floor(offset / 1000) if offset / 1000 > 1 else None
            body_dict = {
                "start": start_time,
                "end": end_time,
                "priority": args.get("priority"),
                "sources": args.get("sources"),
                "tags": args.get("tags"),
                "unaggregated": str_to_bool(args.get("unaggregated")) if args.get("unaggregated") else None,
                "exclude_aggregate": str_to_bool(args.get("exclude_aggregate")) if args.get("exclude_aggregate") else None,
                "page": datadog_page,
            }

            body = {key: value for key, value in body_dict.items() if value is not None}
            response = api_instance.list_events(**body)
            results = response.get("events", [])
            resp = results[offset:offset + limit]
            data = [event.to_dict() for event in resp]
            if data:
                events_list = []
                for event in data:
                    event_dict = event_for_lookup(event)
                    events_list.append(event_dict)
                title = get_command_title_string("Events", page, page_size)
                readable_output = lookup_to_markdown(events_list, title)
            else:
                readable_output = "No Events to present.\n"
        return CommandResults(
            readable_output=readable_output,
            outputs_prefix=f"{INTEGRATION_CONTEXT_NAME}.Event",
            outputs_key_field="id",
            outputs=data,
        )




""" MAIN FUNCTION """


def main() -> None:
    command: str = demisto.command()
    params: Dict[str, Any] = demisto.params()
    args: Dict[str, Any] = demisto.args()

    demisto.debug(f"Command being called is {command}")
    try:
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = params.get('api_key') #"9a2e2f79385b2b996b45df7930bd8c6a"
        configuration.api_key[
            "appKeyAuth"] = params.get('app_key') #"2e28f1d651459c5bbb5bb26826cbbbc2a1d3de64"
        # configuration.server_variables["site"] = params.get('site')

        commands = {
            "datadog-event-create":
                create_event_command,
            "datadog-event-list":
                get_events_command,
        }
        if command == "test-module":
            return_results(test_module(configuration))
        elif command in commands:
            return_results(commands[command](configuration, args))
        else:
            raise NotImplementedError
        # Log exceptions
    except Exception as e:
        return_error(
            f'Failed to execute {command} command. Error: {str(e)}')


""" ENTRY POINT """

if __name__ in ("__main__", "__builtin__", "builtins"):
    main()

