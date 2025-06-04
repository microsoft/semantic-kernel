# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime, timedelta
from typing import Annotated

from msgraph import GraphServiceClient
from msgraph.generated.models.booking_appointment import BookingAppointment
from msgraph.generated.models.booking_customer_information import BookingCustomerInformation
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.location import Location

from semantic_kernel.functions.kernel_function_decorator import kernel_function


class BookingsPlugin:
    """A plugin for booking tables at a restaurant."""

    def __init__(
        self,
        graph_client: GraphServiceClient,
        booking_business_id: str,
        booking_service_id: str,
        customer_timezone: str = "America/Chicago",
    ):
        """Initializes a new instance of the BookingsPlugin class.

        Args:
            graph_client (GraphServiceClient): The GraphServiceClient instance.
            booking_business_id (str): The ID of the booking business.
            service_id (str): The ID of the service.
            customer_timezone (str, optional): The timezone of the customer. Defaults to "America/Chicago".
        """
        self.graph_client = graph_client
        self.booking_business_id = booking_business_id
        self.booking_service_id = booking_service_id
        self.customer_timezone = customer_timezone

    @kernel_function(name="book_table", description="Book a table at a restaurant")
    async def book_table(
        self,
        restaurant: Annotated[str, "The name of the restaurant"],
        date_time: Annotated[str, "The time in UTC, formatted as an ISO datetime string, like 2024-09-15T19:00:00"],
        party_size: Annotated[int, "The number of people in the party"],
        customer_name: Annotated[str, "The name of the customer"],
        customer_email: Annotated[str, "The email of the customer"],
        customer_phone: Annotated[str, "The phone number of the customer"],
    ) -> Annotated[str, "The booking appointment ID"]:
        """Book a table at a restaurant.

        Args:
            restaurant (str): The name of the restaurant.
            date_time (datetime): The time in UTC.
            party_size (int): The number of people in the party.
            customer_name (str): The name of the customer.
            customer_email (str): The email of the customer.
            customer_phone (str): The phone number of the customer.

        Returns:
            str: The status of the booking.
        """
        print(f"System > Do you want to book a table at {restaurant} on {date_time} for {party_size} people?")
        print("System > Please confirm by typing 'yes' or 'no'.")
        confirmation = input("User:> ")
        if confirmation.lower() != "yes":
            return "Booking aborted by the user."
        request_body = BookingAppointment(
            odata_type="#microsoft.graph.bookingAppointment",
            customer_time_zone=self.customer_timezone,
            sms_notifications_enabled=False,
            start_date_time=DateTimeTimeZone(
                odata_type="#microsoft.graph.dateTimeTimeZone",
                date_time=date_time,
                time_zone="UTC",
            ),
            end_date_time=DateTimeTimeZone(
                odata_type="#microsoft.graph.dateTimeTimeZone",
                date_time=(datetime.fromisoformat(date_time) + timedelta(hours=2)).isoformat(),
                time_zone="UTC",
            ),
            is_location_online=False,
            opt_out_of_customer_email=False,
            anonymous_join_web_url=None,
            service_id=self.booking_service_id,
            service_location=Location(
                odata_type="#microsoft.graph.location",
                display_name=restaurant,
            ),
            maximum_attendees_count=party_size,
            filled_attendees_count=party_size,
            customers=[
                BookingCustomerInformation(
                    odata_type="#microsoft.graph.bookingCustomerInformation",
                    name=customer_name,
                    email_address=customer_email,
                    phone=customer_phone,
                    time_zone=self.customer_timezone,
                ),
            ],
            additional_data={
                "price_type@odata_type": "#microsoft.graph.bookingPriceType",
                "reminders@odata_type": "#Collection(microsoft.graph.bookingReminder)",
                "customers@odata_type": "#Collection(microsoft.graph.bookingCustomerInformation)",
            },
        )

        response = await self.graph_client.solutions.booking_businesses.by_booking_business_id(
            self.booking_business_id
        ).appointments.post(request_body)

        return f"Booking successful! Your reservation ID is {response.id}."

    @kernel_function(name="list_revervations", description="List all reservations")
    async def list_reservations(self) -> Annotated[str, "The list of reservations"]:
        """List the reservations for the booking business."""
        appointments = await self.graph_client.solutions.booking_businesses.by_booking_business_id(
            self.booking_business_id
        ).appointments.get()
        return "\n".join([
            f"{appointment.service_location.display_name} on {appointment.start_date_time.date_time} with id: {appointment.id}"  # noqa: E501
            for appointment in appointments.value
        ])

    @kernel_function(name="cancel_reservation", description="Cancel a reservation")
    async def cancel_reservation(
        self,
        reservation_id: Annotated[str, "The ID of the reservation"],
        restaurant: Annotated[str, "The name of the restaurant"],
        date: Annotated[str, "The date of the reservation"],
        time: Annotated[str, "The time of the reservation"],
        party_size: Annotated[int, "The number of people in the party"],
    ) -> Annotated[str, "The cancellation status of the reservation"]:
        """Cancel a reservation."""
        print(f"System > [Cancelling a reservation for {party_size} at {restaurant} on {date} at {time}]")

        _ = (
            await self.graph_client.solutions.booking_businesses.by_booking_business_id(self.booking_business_id)
            .appointments.by_booking_appointment_id(reservation_id)
            .delete()
        )
        return "Cancellation successful!"
