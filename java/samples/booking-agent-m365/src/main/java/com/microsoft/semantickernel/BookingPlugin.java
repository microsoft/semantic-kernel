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
import java.util.List;

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
        @KernelFunctionParameter(name = "partySize", description = "The number of people in the party", type = int.class) int partySize) {
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

        graphServiceClient.solutions().bookingBusinesses().byBookingBusinessId(bookingBusinessId)
            .appointments().post(bookingAppointment);

        return "Successful booking at " + restaurant;
    }

    @DefineKernelFunction(name = "listReservations", description = "List all reservations for a restaurant", returnType = "string")
    public String listReservations(
        @KernelFunctionParameter(name = "restaurant", description = "The name of the restaurant") String restaurant) {
        List<BookingAppointment> appointments = graphServiceClient.solutions().bookingBusinesses()
            .byBookingBusinessId(bookingBusinessId).appointments().get().getValue();

        StringBuilder appointmentsList = new StringBuilder();
        for (BookingAppointment appointment : appointments) {
            if (appointment.getServiceLocation().getDisplayName().equals(restaurant)) {
                appointmentsList.append(appointment.getServiceLocation().getDisplayName())
                    .append(" at ")
                    .append(appointment.getStartDateTime().getDateTime())
                    .append(" for ")
                    .append(appointment.getMaximumAttendeesCount())
                    .append(" people\n");
            }
        }

        if (appointmentsList.toString().isEmpty()) {
            return "No reservations found for " + restaurant;
        }

        return appointmentsList.toString();
    }

    private BookingAppointment getAppointment(String restaurant, OffsetDateTime date) {
        List<BookingAppointment> appointments = graphServiceClient.solutions().bookingBusinesses()
            .byBookingBusinessId(bookingBusinessId).appointments().get().getValue();

        for (BookingAppointment appointment : appointments) {
            if (appointment.getServiceLocation().getDisplayName().equals(restaurant)
                && OffsetDateTime.parse(appointment.getStartDateTime().getDateTime())
                    .equals(date)) {
                return appointment;
            }
        }

        return null;
    }

    @DefineKernelFunction(name = "modifyReservation", description = "Modify an existing reservation at a restaurant", returnType = "string")
    public String modifyReservation(
        @KernelFunctionParameter(name = "restaurant", description = "The name of the restaurant") String restaurant,
        @KernelFunctionParameter(name = "date", description = "The date of the reservation in UTC", type = OffsetDateTime.class) OffsetDateTime date,
        @KernelFunctionParameter(name = "updatedDate", description = "The updated date of the reservation in UTC", type = OffsetDateTime.class) OffsetDateTime updatedDate) {
        BookingAppointment appointment = getAppointment(restaurant, date);
        if (appointment == null) {
            return "No reservation found for " + restaurant + " on " + date;
        }

        appointment.setStartDateTime(new DateTimeTimeZone() {
            {
                setDateTime(updatedDate.toString());
                setTimeZone("UTC");
            }
        });
        appointment.setEndDateTime(new DateTimeTimeZone() {
            {
                setDateTime(updatedDate.plusHours(BOOKING_HOURS).toString());
                setTimeZone("UTC");
            }
        });

        graphServiceClient.solutions().bookingBusinesses().byBookingBusinessId(bookingBusinessId)
            .appointments().byBookingAppointmentId(appointment.getId()).patch(appointment);

        return "Reservation updated at " + restaurant + " from " + date + " to " + updatedDate;
    }

    @DefineKernelFunction(name = "cancelReservation", description = "Cancel a reservation at a restaurant", returnType = "string")
    public String cancelReservation(
        @KernelFunctionParameter(name = "restaurant", description = "The name of the restaurant") String restaurant,
        @KernelFunctionParameter(name = "date", description = "The date of the reservation in UTC", type = OffsetDateTime.class) OffsetDateTime date) {
        BookingAppointment appointment = getAppointment(restaurant, date);
        if (appointment == null) {
            return "No reservation found for " + restaurant + " on " + date;
        }

        graphServiceClient.solutions().bookingBusinesses().byBookingBusinessId(bookingBusinessId)
            .appointments().byBookingAppointmentId(appointment.getId()).delete();

        return "Reservation cancelled at " + restaurant + " on " + date;
    }
}
