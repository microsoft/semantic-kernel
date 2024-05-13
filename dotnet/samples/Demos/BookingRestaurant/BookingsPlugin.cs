// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Graph;
using Microsoft.Graph.Models;
using Microsoft.SemanticKernel;

namespace Plugins;

/// <summary>
/// Booking Plugin with specialized functions for booking a table at a restaurant using Microsoft Graph Bookings API.
/// </summary>
internal sealed class BookingsPlugin
{
    private readonly GraphServiceClient _graphClient;
    private readonly string _businessId;
    private readonly string _customerTimeZone;
    private readonly string _serviceId;

    private const int PostBufferMinutes = 10;
    private const int PreBufferMinutes = 5;

    internal BookingsPlugin(
        GraphServiceClient graphClient,
        string businessId,
        string serviceId,
        string customerTimeZone = "America/Chicago"
    )
    {
        this._graphClient = graphClient;
        this._businessId = businessId;
        this._serviceId = serviceId;
        this._customerTimeZone = customerTimeZone;
    }

    [KernelFunction("BookTable")]
    [Description("Books a new table at a restaurant")]
    public async Task<string> BookTableAsync(
        [Description("Name of the restaurant")] string restaurant,
        [Description("The time in UTC")] DateTime dateTime,
        [Description("Number of people in your party")] int partySize,
        [Description("Customer name")] string customerName,
        [Description("Customer email")] string customerEmail,
        [Description("Customer phone number")] string customerPhone
    )
    {
        Console.WriteLine($"System > Do you want to book a table at {restaurant} on {dateTime} for {partySize} people?");
        Console.WriteLine("System > Please confirm by typing 'yes' or 'no'.");
        Console.Write("User > ");
        var response = Console.ReadLine()?.Trim();
        if (string.Equals(response, "yes", StringComparison.OrdinalIgnoreCase))
        {
            var requestBody = new BookingAppointment
            {
                OdataType = "#microsoft.graph.bookingAppointment",
                CustomerTimeZone = this._customerTimeZone,
                SmsNotificationsEnabled = false,
                EndDateTime = new DateTimeTimeZone
                {
                    OdataType = "#microsoft.graph.dateTimeTimeZone",
                    DateTime = dateTime.AddHours(2).ToString("o"),
                    TimeZone = "UTC",
                },
                IsLocationOnline = false,
                OptOutOfCustomerEmail = false,
                AnonymousJoinWebUrl = null,
                PostBuffer = TimeSpan.FromMinutes(PostBufferMinutes),
                PreBuffer = TimeSpan.FromMinutes(PreBufferMinutes),
                ServiceId = this._serviceId,
                ServiceLocation = new Location
                {
                    OdataType = "#microsoft.graph.location",
                    DisplayName = restaurant,
                },
                StartDateTime = new DateTimeTimeZone
                {
                    OdataType = "#microsoft.graph.dateTimeTimeZone",
                    DateTime = dateTime.ToString("o"),
                    TimeZone = "UTC",
                },
                MaximumAttendeesCount = partySize,
                FilledAttendeesCount = partySize,
                Customers =
                [
                    new BookingCustomerInformation
                    {
                        OdataType = "#microsoft.graph.bookingCustomerInformation",
                        Name = customerName,
                        EmailAddress = customerEmail,
                        Phone = customerPhone,
                        TimeZone = this._customerTimeZone,
                    },
                ],
                AdditionalData = new Dictionary<string, object>
                {
                    ["priceType@odata.type"] = "#microsoft.graph.bookingPriceType",
                    ["reminders@odata.type"] = "#Collection(microsoft.graph.bookingReminder)",
                    ["customers@odata.type"] = "#Collection(microsoft.graph.bookingCustomerInformation)"
                },
            };

            // list service IDs
            var services = await this._graphClient.Solutions.BookingBusinesses[this._businessId].Services.GetAsync();

            // To initialize your graphClient, see https://learn.microsoft.com/en-us/graph/sdks/create-client?from=snippets&tabs=csharp
            var result = await this._graphClient.Solutions.BookingBusinesses[this._businessId].Appointments.PostAsync(requestBody);

            return "Booking successful!";
        }

        return "Booking aborted by the user";
    }

    [KernelFunction]
    [Description("List reservations booking at a restaurant.")]
    public async Task<List<Appointment>> ListReservationsAsync()
    {
        // Print the booking details to the console
        var resultList = new List<Appointment>();
        var appointments = await this._graphClient.Solutions.BookingBusinesses[this._businessId].Appointments.GetAsync();

        foreach (var appointmentResponse in appointments?.Value!)
        {
            resultList.Add(new Appointment(appointmentResponse));
        }

        return resultList;
    }

    [KernelFunction]
    [Description("Cancels a reservation at a restaurant.")]
    public async Task<string> CancelReservationAsync(
        [Description("The appointment ID to cancel")] string appointmentId,
        [Description("Name of the restaurant")] string restaurant,
        [Description("The date of the reservation")] string date,
        [Description("The time of the reservation")] string time,
        [Description("Number of people in your party")] int partySize)
    {
        // Print the booking details to the console
        Console.ForegroundColor = ConsoleColor.DarkBlue;
        Console.WriteLine($"System > [Cancelling a reservation for {partySize} at {restaurant} on {date} at {time}]");
        Console.ResetColor();

        await this._graphClient.Solutions.BookingBusinesses[this._businessId].Appointments[appointmentId].DeleteAsync();

        return "Cancellation successful!";
    }
}
