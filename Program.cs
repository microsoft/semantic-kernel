
using Microsoft.OpenApi.Models;
using System;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json;
using System.Collections.Generic;
using Azure.Storage.Blobs;
using Azure.Storage.Blobs.Models;



var builder = WebApplication.CreateBuilder(args);
// HttpClient client = new HttpClient();

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { Title = "Port Authority of New York and New Jersey API", Description = "API that provides various information for the Port Authority of New York and New Jersey", Version = "v1" });
});

var app = builder.Build();

// Configure the HTTP request pipeline.
// if (app.Environment.IsDevelopment())
//     { }

app.UseSwagger(c =>
    {
        c.PreSerializeFilters.Add((swagger, httpReq) =>
        {
            swagger.Servers = new List<OpenApiServer>
            {
                    // new OpenApiServer { Url = $"{httpReq.Scheme}://{httpReq.Host.Value}" }
                    new OpenApiServer { Url = $"http://localhost:5178" }

            };
        });
    });
app.UseSwaggerUI();
app.UseStaticFiles();

//app.UseHttpsRedirection();

app.MapGet("/SecurityTimes/{airportCode}", async (string airportCode) =>
{
    string jsonFileSuffix = "SecurityTimes.json";
    string blobContents = await GetBlobContents(airportCode, jsonFileSuffix);
    return blobContents;
})
.WithDescription("Calculates the TSA Security time for an airport when provided a 3 digit code as a string")
.WithName("Security TSA Wait Time")
.WithOpenApi();

app.MapGet("/TaxiWaitTimes/{airportCode}", async (string airportCode) =>
{

    string jsonFileSuffix = "TaxiWaitTimes.json";
    string blobContents = await GetBlobContents(airportCode, jsonFileSuffix);
    return blobContents;
})
.WithDescription("Calculates the Average Wait  Time for taxi at terminals for an airport when provided a 3 digit code as a string")
.WithName("Taxi Wait Time at Terminals")
.WithOpenApi();

app.MapGet("/ParkingWaitTimes/{airportCode}", async (string airportCode) =>
{

    string jsonFileSuffix = "ParkingWaitTimes.json";
    string blobContents = await GetBlobContents(airportCode, jsonFileSuffix);
    return blobContents;
})
.WithDescription("Calculates the Average Wait of Parking spaces at Terminals for an airport when provided a 3 digit code as a string")
.WithName("Parking Wait Time to Gates")
.WithOpenApi();

app.MapGet("/WalkTime/{airportCode}", async (string airportCode) =>
{

    string jsonFileSuffix = "WalkTimes.json";
    string blobContents = await GetBlobContents(airportCode, jsonFileSuffix);
    return blobContents;
})
.WithDescription("Calculates the Average Walk Time to Gates from Terminal Security Checkpoint for an airport when provided a 3 digit code as a string")
.WithName("Walk Time to Gates")
.WithOpenApi();

app.MapGet("/FlightTracker/{airportCode}", async (string airportCode) =>
{

    string jsonFileSuffix = "FlightTracker.json";
    string blobContents = await GetBlobContents(airportCode, jsonFileSuffix);
    return blobContents;
})
.WithDescription("Calculates the Average Walk Time to Gates from Terminal Security Checkpoint for an airport when provided a 3 digit code as a string")
.WithName("Flight Tracker Info")
.WithOpenApi();

// EXAMPLE FLIGHT REQUESThttps://www.tsawaittimes.com/
// https://api.aviationstack.com/v1/flights?access_key=38b6e3206fde528c672437dfd815c329&limit=10&airline_iata=AA&flight_number=76
// Requests American Airlines Flight 76 - which is out of JFK en route to SFO
app.MapGet("/FlightStatus/{airline_iata}/{flight_number}", async (string flight_number, string airline_iata) =>
{

    string? access_key = app.Configuration["APIKeyAviationStack"];
    app.Logger.LogInformation("FlightStatus endpoint called with Flight Number: {0}{1} ", airline_iata, flight_number);
    var outputString = "Error";
    using (var client = new HttpClient())
    {
        try
        {
            var urlString = string.Format("https://api.aviationstack.com/v1/flights?access_key={0}&airline_iata={1}&flight_number={2}&limit=3", access_key, airline_iata, flight_number);
            using HttpResponseMessage response = await client.GetAsync(urlString);
            response.EnsureSuccessStatusCode();

            string responseBody = await response.Content.ReadAsStringAsync();

            dynamic? apiResponse = JsonConvert.DeserializeObject(responseBody);

            if (apiResponse!.data.Count > 0)
            {
                dynamic firstFlight = apiResponse.data[0];
                var propertyValue = firstFlight.propertyName;
                Console.WriteLine($"First flight: {firstFlight}");
                var departure_terminal = firstFlight.departure.terminal;
                var departure_gate = firstFlight.departure.gate;
                var departure_airport = firstFlight.departure.airport;
                var ddtString = firstFlight.departure.estimated;
                DateTime departure_dt = DateTime.Parse(ddtString.ToString()).ToLocalTime();
                string formatted_departure = departure_dt.ToString("MM/dd/yyyy HH:mm:ss tt").ToString();

                var arrival_gate = firstFlight.arrival.gate;
                var arrival_airport = firstFlight.arrival.airport;
                var adtString = firstFlight.arrival.estimated;
                DateTime arrival_dt = DateTime.Parse(adtString.ToString()).ToLocalTime();
                string formatted_arrival = arrival_dt.ToString("MM/dd/yyyy HH:mm:ss tt").ToString();

                outputString = string.Format("{0} flight {1} is estimated to depart from terminal {7} gate {2} from {3} Airport at {4} and estimated to arrive at {5} Airport at {6}.", airline_iata, flight_number, departure_gate, departure_airport, formatted_departure, arrival_airport, formatted_arrival, departure_terminal);
                Console.WriteLine(outputString);
                outputString = firstFlight.ToString();
                return outputString;
            }
        }
        catch (HttpRequestException e)
        {
            Console.WriteLine("\nException Caught!");
            outputString = string.Format("Message :{0} ", e);
        }
    }

    return outputString;


})
.WithDescription("Returns the Flight Status for flight when provided an airline code and flight number by string")
.WithName("Flight Status API")
.WithOpenApi();




app.Run();

int TSAWait(string airportCode, string terminal)
{
    Random random = new();
    int waitTime = 0;
    string airportCodeUpper = airportCode.ToUpper();

    switch (airportCodeUpper)
    {
        case "EWR":
            waitTime = random.Next(10, 16);
            break;
        case "LGA":
            waitTime = random.Next(20, 30);
            break;
        case "JFK":
            waitTime = random.Next(35, 46);
            if (terminal == "1")
            {
                waitTime = waitTime + 0;
            }
            else if (terminal == "4")
            {
                waitTime = waitTime + 4;
            }
            else if (terminal == "5")
            {
                waitTime = waitTime - 5;
            }
            else if (terminal == "7")
            {
                waitTime = waitTime + 9;
            }
            else if (terminal == "8")
            {
                waitTime = waitTime + 13;
            }
            break;
        default:
            waitTime = 2;
            break;
    }

    double TimeOfDayFactor = CalcTimeOfDayFactor();
    waitTime = (int)(waitTime * TimeOfDayFactor);

    return waitTime;
}

int WalkTime(string airportCode)
{
    Random random = new();
    int walkTime = 0;
    string airportCodeUpper = airportCode.ToUpper();

    switch (airportCodeUpper)
    {
        case "EWR":
            walkTime = random.Next(3, 8);
            break;
        case "LGA":
            walkTime = random.Next(9, 12);
            break;
        case "JFK":
            walkTime = random.Next(13, 15);
            break;
        default:
            walkTime = 2;
            break;
    }

    double TimeOfDayFactor = CalcTimeOfDayFactor();
    walkTime = (int)(walkTime * TimeOfDayFactor);

    return walkTime;
}

// string TravelerTimeToAirport(string airline, string flightNumber)
// {
//     string airlineUpper = airline.ToUpper();
//     string flightNumberUpper = flightNumber.ToUpper();
//     string estArrivalTime = "ETA not set";
//     string airportCode = "";
//     int tsaWaitTime = 0;
//     int walkTime = 0;
//     DateTime ScheduledDepartureTime = DateTime.Now;
//     DateTime EstimatedTravelerTimeToAirport = DateTime.Now;

//     switch (airlineUpper)
//     {
//         case "JETBLUE":
//             if (flightNumberUpper == "61613")
//             {
//                 //JetBlue 61613, New York, JFK to Los Angeles, LAX, Scheduled departure 9:27 am
//                 ScheduledDepartureTime = new DateTime(DateTime.Now.Year, DateTime.Now.Month, DateTime.Now.Day, 9, 27, 0);
//                 airportCode = "JFK";
//                 tsaWaitTime = TSAWait(airportCode);
//                 walkTime = WalkTime(airportCode);

//                 EstimatedTravelerTimeToAirport = ScheduledDepartureTime.AddMinutes(-(tsaWaitTime + walkTime));
//                 estArrivalTime = EstimatedTravelerTimeToAirport.ToString("hh:mm tt");

//             }
//             break;
//         default:
//             estArrivalTime = "Flight not found";
//             break;
//     }

//     app.Logger.LogInformation("TravelerTimeToAirport: {airportCode}, {tsaWaitTime}, {walkTime},{ScheduledDepartureTime},{EstimatedTravelerTimeToAirport}", airportCode, tsaWaitTime, walkTime, ScheduledDepartureTime, EstimatedTravelerTimeToAirport);

//     return estArrivalTime;
// }


static double CalcTimeOfDayFactor()
{
    DateTime now = DateTime.Now;
    TimeSpan factorEarlyMorning = new(6, 0, 0); // 6 AM
    TimeSpan factorLateMorning = new(10, 0, 0); // 10 AM
    TimeSpan factorAfternoon = new(15, 0, 0); // 3 PM
    TimeSpan factorLateNight = new(22, 0, 0); // 10 PM  
    TimeSpan nowTime = now.TimeOfDay;
    double TimeOfDayFactor = 1.0;

    if ((nowTime > factorEarlyMorning) && (nowTime < factorLateMorning))
    {
        // morning rush
        TimeOfDayFactor = 1.8;
    }
    else if ((nowTime > factorLateMorning) && (nowTime < factorAfternoon))
    {
        // mid day slow down
        TimeOfDayFactor = 1.2;
    }
    else if ((nowTime > factorAfternoon) && (nowTime < factorLateNight))
    {
        // end of day rush
        TimeOfDayFactor = 1.5;
    }
    else
    {
        // overnight slow down
        TimeOfDayFactor = .8;
    }

    return TimeOfDayFactor;
}




async Task<string> GetBlobContents(string airportCode, string jsonFileSuffix)
{

    // retrieve Azure Storage items from settings (in development, keys in secrets.json )
    string? connectionString = app.Configuration["AzureBlobStorage:ConnectionString"];
    string? containerName = app.Configuration["AzureBlobStorage:ContainerName"];
    string upperAirportCode = airportCode.ToUpper();

    // Create a BlobServiceClient
    BlobServiceClient blobServiceClient = new BlobServiceClient(connectionString);

    // Create a BlobContainerClient
    BlobContainerClient containerClient = blobServiceClient.GetBlobContainerClient(containerName);

    // Create a BlobClient
    string jsonFileName = upperAirportCode + jsonFileSuffix;
    BlobClient blobClient = containerClient.GetBlobClient(jsonFileName);

    // Check if the blob exists
    if (await blobClient.ExistsAsync())
    {
        // Download the blob content
        BlobDownloadResult downloadResult = await blobClient.DownloadContentAsync();
        string blobContents = downloadResult.Content.ToString();

        //app.Logger.LogInformation($"jsonFileName: {jsonFileName}");
        app.Logger.LogInformation($"blobContents: {blobContents}");

        return blobContents;
    }
    else
    {
        app.Logger.LogInformation($"Blob not found: {jsonFileName}");
        return "{}";
    }

}


