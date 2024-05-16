// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.graph.models.BookingAppointment;
import com.microsoft.graph.models.BookingCustomerInformation;
import com.microsoft.graph.models.BookingCustomerInformationBase;
import com.microsoft.graph.models.DateTimeTimeZone;
import com.microsoft.graph.models.Location;
import com.microsoft.graph.models.User;
import com.microsoft.graph.serviceclient.GraphServiceClient;
import com.microsoft.kiota.PeriodAndDuration;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;

import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

public class BookingPlugin {
    public static final int BOOKING_HOURS = 2;
    private final GraphServiceClient graphServiceClient;
    private final String bookingBusinessId;
    private final String serviceId;
    private final String userTimeZone;

    public BookingPlugin(GraphServiceClient graphServiceClient,
        String bookingBusinessId,
        String serviceId,
        String userTimeZone) {
        this.graphServiceClient = graphServiceClient;
        this.bookingBusinessId = bookingBusinessId;
        this.serviceId = serviceId;
        this.userTimeZone = userTimeZone;
    }

    @DefineKernelFunction(name = "bookTable", description = "Book a table at a restaurant", returnType = "string")
    public String bookTable(
        @KernelFunctionParameter(name = "restaurant", description = "The name of the restaurant") String restaurant,
        @KernelFunctionParameter(name = "date", description = "The date of the reservation in UTC", type = OffsetDateTime.class) OffsetDateTime date,
        @KernelFunctionParameter(name = "partySize", description = "The number of people in the party", type = int.class) int partySize,
        @KernelFunctionParameter(name = "customerName", description = "The name of the customer") String customerName,
        @KernelFunctionParameter(name = "customerEmail", description = "The email of the customer") String customerEmail,
        @KernelFunctionParameter(name = "customerPhone", description = "The phone of the customer") String customerPhone
        ) {
        System.out.println("System > Do you want to book a table at " + restaurant + " on " + date + " for " + partySize + " people?");
        System.out.println("System > Please confirm the booking by typing 'yes' or 'no'");
        Scanner scanner = new Scanner(System.in);
        String response = scanner.nextLine().toLowerCase();

        if (response.equals("yes")) {
            BookingAppointment bookingAppointment = new BookingAppointment();
            bookingAppointment.setOdataType("#microsoft.graph.bookingAppointment");
            bookingAppointment.setCustomerTimeZone(userTimeZone);
            bookingAppointment.setSmsNotificationsEnabled(false);
            DateTimeTimeZone endDateTime = new DateTimeTimeZone();
            endDateTime.setOdataType("#microsoft.graph.dateTimeTimeZone");
            endDateTime.setDateTime(date.plusHours(BOOKING_HOURS).toString());
            endDateTime.setTimeZone("UTC");
            bookingAppointment.setEndDateTime(endDateTime);
            bookingAppointment.setIsLocationOnline(false);
            bookingAppointment.setOptOutOfCustomerEmail(false);
            bookingAppointment.setAnonymousJoinWebUrl(null);
            PeriodAndDuration postBuffer = PeriodAndDuration.ofDuration(Duration.parse("PT10M"));
            bookingAppointment.setPostBuffer(postBuffer);
            PeriodAndDuration preBuffer = PeriodAndDuration.ofDuration(Duration.parse("PT5M"));
            bookingAppointment.setPreBuffer(preBuffer);
            bookingAppointment.setServiceId(serviceId);
            Location serviceLocation = new Location();
            serviceLocation.setOdataType("#microsoft.graph.location");
            serviceLocation.setDisplayName(restaurant);
            bookingAppointment.setServiceLocation(serviceLocation);
            DateTimeTimeZone startDateTime = new DateTimeTimeZone();
            startDateTime.setOdataType("#microsoft.graph.dateTimeTimeZone");
            startDateTime.setDateTime(date.toString());
            startDateTime.setTimeZone("UTC");
            bookingAppointment.setStartDateTime(startDateTime);
            bookingAppointment.setMaximumAttendeesCount(partySize);
            bookingAppointment.setFilledAttendeesCount(partySize);
            bookingAppointment.setCustomers(List.of(new BookingCustomerInformation() {
                {
                    setOdataType("#microsoft.graph.bookingCustomerInformation");
                    new BookingCustomerInformationBase() {
                        {
                            setOdataType("#microsoft.graph.bookingCustomerInformationBase");
                            setName(customerName);
                            setEmailAddress(customerEmail);
                            setPhone(customerPhone);
                        }
                    };
                }
            }));

            graphServiceClient.solutions().bookingBusinesses().byBookingBusinessId(bookingBusinessId)
                    .appointments().post(bookingAppointment);

            return "Booking successful!";
        }

        return "Booking aborted by the user";
    }

    @DefineKernelFunction(name = "listReservations", description = "List all reservations for a customer")
    public List<String> listReservations(
            @KernelFunctionParameter(name = "customerName", description = "The name of the customer") String customerName) {
        List<BookingAppointment> appointments = graphServiceClient.solutions().bookingBusinesses()
                .byBookingBusinessId(bookingBusinessId).appointments().get().getValue();

        List<String> reservations = new ArrayList<>();
        for (BookingAppointment appointment : appointments) {
            if (appointment.getCustomers() != null && !appointment.getCustomers().isEmpty() &&
                    appointment.getCustomers().get(0).getBackingStore().get("name").equals(customerName)) {
                String reservation = "Restaurant: " +
                        appointment.getServiceLocation().getDisplayName() +
                        "Date: " +
                        appointment.getStartDateTime().getDateTime() +
                        "Party size: " +
                        appointment.getMaximumAttendeesCount();

                reservations.add(reservation);
            }
        }

        return reservations;
    }

    private BookingAppointment getAppointment(String restaurant, String customerName, OffsetDateTime date) {
        List<BookingAppointment> appointments = graphServiceClient.solutions().bookingBusinesses()
            .byBookingBusinessId(bookingBusinessId).appointments().get().getValue();

        for (BookingAppointment appointment : appointments) {
            if (appointment.getServiceLocation().getDisplayName().equals(restaurant)
                    && appointment.getCustomers() != null && !appointment.getCustomers().isEmpty()
                    && appointment.getCustomers().get(0).getBackingStore().get("name").equals(customerName)
                    && OffsetDateTime.parse(appointment.getStartDateTime().getDateTime())
                    .equals(date)) {
                return appointment;
            }
        }
        return null;
    }

    @DefineKernelFunction(name = "cancelReservation", description = "Cancel a reservation at a restaurant", returnType = "string")
    public String cancelReservation(
        @KernelFunctionParameter(name = "restaurant", description = "The name of the restaurant") String restaurant,
        @KernelFunctionParameter(name = "date", description = "The date of the reservation in UTC", type = OffsetDateTime.class) OffsetDateTime date,
        @KernelFunctionParameter(name = "customerName", description = "The name of the customer") String customerName) {

        System.out.println("System > [Cancelling a reservation for " + customerName + " at " + restaurant + " on " + date + "]");
        BookingAppointment appointment = getAppointment(restaurant, customerName, date);

        graphServiceClient.solutions().bookingBusinesses().byBookingBusinessId(bookingBusinessId)
            .appointments().byBookingAppointmentId(appointment.getId()).delete();

        return "Reservation cancelled";
    }
}
