# Copyright (c) Microsoft. All rights reserved.

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from msgraph import GraphServiceClient
from msgraph.generated.models.booking_appointment import BookingAppointment
from msgraph.generated.models.booking_customer_information import \
    BookingCustomerInformation
from msgraph.generated.models.booking_customer_information_base import \
    BookingCustomerInformationBase
from msgraph.generated.models.booking_question_answer import \
    BookingQuestionAnswer
from msgraph.generated.models.booking_reminder import BookingReminder
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.location import Location
from msgraph.generated.models.outlook_geo_coordinates import \
    OutlookGeoCoordinates
from msgraph.generated.models.physical_address import PhysicalAddress

from semantic_kernel.functions.kernel_function_decorator import kernel_function


class BookingsPlugin:

    def __init__(self, graph_client: GraphServiceClient, booking_business_id: str, service_id: str, customer_timezone: str = "America/New_York"):
        self.graph_client = graph_client
        self.booking_business_id = booking_business_id
        self.service_id = service_id
        self.customer_timezone = customer_timezone
