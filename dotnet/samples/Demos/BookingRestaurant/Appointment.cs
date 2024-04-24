// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Graph.Models;

namespace Plugins;

/// <summary>
/// This class represents an appointment model for the booking plugin.
/// </summary>
internal sealed class Appointment
{
    internal Appointment(BookingAppointment bookingAppointment)
    {
        this.Start = bookingAppointment.StartDateTime.ToDateTime();
        this.Restaurant = bookingAppointment.ServiceLocation?.DisplayName ?? "";
        this.PartySize = bookingAppointment.MaximumAttendeesCount ?? 0;
        this.ReservationId = bookingAppointment.Id;
    }

    public DateTime Start { get; set; }
    public string? Restaurant { get; set; }
    public int PartySize { get; set; }
    public string? ReservationId { get; set; }
}
