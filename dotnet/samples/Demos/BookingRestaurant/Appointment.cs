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

    /// <summary>
    /// Start date and time of the appointment.
    /// </summary>
    public DateTime Start { get; set; }

    /// <summary>
    /// The restaurant name.
    /// </summary>
    public string? Restaurant { get; set; }

    /// <summary>
    /// Number of people in the party.
    /// </summary>
    public int PartySize { get; set; }

    /// <summary>
    /// The reservation id.
    /// </summary>
    public string? ReservationId { get; set; }
}
