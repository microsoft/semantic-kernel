// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Skills.Weather.WeatherApi;

/// <summary>
/// Bing API connector.
/// </summary>
public sealed class WeatherApiConnector : IWeatherApiConnector, IDisposable
{
    private readonly ILogger _logger;
    private readonly HttpClientHandler _httpClientHandler;
    private readonly HttpClient _httpClient;

    private string ApiKey { get; set; } = string.Empty;
    private const string BaseUrl = "http://api.weatherapi.com/v1/current.json";

    public WeatherApiConnector(string apiKey, ILogger<WeatherApiConnector>? logger = null)
    {
        this._logger = logger ?? NullLogger<WeatherApiConnector>.Instance;
        this._httpClientHandler = new() { CheckCertificateRevocationList = true };
        this._httpClient = new HttpClient(this._httpClientHandler);
        ApiKey = apiKey;
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<string>> LookupWeatherAsync(string city, int count = 1, int offset = 0, CancellationToken cancellationToken = default)
    {
        if (count <= 0) { throw new ArgumentOutOfRangeException(nameof(count)); }

        if (count >= 50) { throw new ArgumentOutOfRangeException(nameof(count), $"{nameof(count)} value must be less than 50."); }

        if (offset < 0) { throw new ArgumentOutOfRangeException(nameof(offset)); }

        Uri uri = new Uri($"{BaseUrl}?key={ApiKey}&q={Uri.EscapeDataString(city)}");

        this._logger.LogDebug("Sending request: {0}", uri);
        HttpResponseMessage response = await this._httpClient.GetAsync(uri, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        this._logger.LogDebug("Response received: {0}", response.StatusCode);

        string json = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        //Console.WriteLine("Response content received: {0}", json);

        this._logger.LogTrace("Response content received: {0}", json);
        var data = JsonSerializer.Deserialize<WeatherApiResponse>(json);

        //Console.WriteLine($"weather in ${city} is ${data?.CurrentWeather?.Condition?.Text}");

        String[]? results = new String[] { data?.CurrentWeather?.Condition?.Text };

        return results == null ? Enumerable.Empty<string>() : results;
    }

    /*
    {
        "location": {
            "name": "Redmond",
            "region": "Washington",
            "country": "United States of America",
            "lat": 47.67,
            "lon": -122.12,
            "tz_id": "America/Los_Angeles",
            "localtime_epoch": 1686178372,
            "localtime": "2023-06-07 15:52"
        },
        "current": {
            "last_updated_epoch": 1686177900,
            "last_updated": "2023-06-07 15:45",
            "temp_c": 28.9,
            "temp_f": 84,
            "is_day": 1,
            "condition": {
                "text": "Sunny",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/113.png",
                "code": 1000
            },
            "wind_mph": 6.9,
            "wind_kph": 11.2,
            "wind_degree": 360,
            "wind_dir": "N",
            "pressure_mb": 1010,
            "pressure_in": 29.81,
            "precip_mm": 0,
            "precip_in": 0,
            "humidity": 28,
            "cloud": 0,
            "feelslike_c": 26.9,
            "feelslike_f": 80.5,
            "vis_km": 16,
            "vis_miles": 9,
            "uv": 8,
            "gust_mph": 6.3,
            "gust_kph": 10.1
        }
    }


    {
    "location": {
        "name": "Ares",
        "region": "Galicia",
        "country": "Spain",
        "lat": 43.43,
        "lon": -8.23,
        "tz_id": "Europe/Madrid",
        "localtime_epoch": 1686178427,
        "localtime": "2023-06-08 0:53"
    },
    "current": {
        "last_updated_epoch": 1686177900,
        "last_updated": "2023-06-08 00:45",
        "temp_c": 18,
        "temp_f": 64.4,
        "is_day": 0,
        "condition": {
            "text": "Moderate rain",
            "icon": "//cdn.weatherapi.com/weather/64x64/night/302.png",
            "code": 1189
        },
        "wind_mph": 2.2,
        "wind_kph": 3.6,
        "wind_degree": 10,
        "wind_dir": "N",
        "pressure_mb": 1008,
        "pressure_in": 29.77,
        "precip_mm": 0.2,
        "precip_in": 0.01,
        "humidity": 100,
        "cloud": 25,
        "feelslike_c": 18,
        "feelslike_f": 64.4,
        "vis_km": 10,
        "vis_miles": 6,
        "uv": 1,
        "gust_mph": 13.9,
        "gust_kph": 22.3
    }
}
    */

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._httpClient.Dispose();
            this._httpClientHandler.Dispose();
        }
    }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    public Task<IEnumerable<string>> SearchAsync(string location, int count = 1, int offset = 0, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    [SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
        Justification = "Class is instantiated through deserialization.")]
    private sealed class WeatherApiResponse
    {
        [JsonPropertyName("location")]
        public Location? Location { get; set; }

        [JsonPropertyName("current")]
        public WeatherReport? CurrentWeather { get; set; }
    }


    /*
    "location": {
            "name": "Ares",
            "region": "Galicia",
            "country": "Spain",
            "lat": 43.43,
            "lon": -8.23,
            "tz_id": "Europe/Madrid",
            "localtime_epoch": 1686178427,
            "localtime": "2023-06-08 0:53"
        },
    */
    [SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
        Justification = "Class is instantiated through deserialization.")]
    private sealed class Location
    {
        [JsonPropertyName("name")]
        public String? Name { get; set; }

        [JsonPropertyName("region")]
        public String? Region { get; set; }

        [JsonPropertyName("country")]
        public String? Country { get; set; }

        [JsonPropertyName("lat")]
        public float? Latitude { get; set; }

        [JsonPropertyName("lon")]
        public float? Longitude { get; set; }

        [JsonPropertyName("tz_id")]
        public String? TimeZoneId { get; set; }

        [JsonPropertyName("localtime_epoch")]
        public float? LocalTimeEpoch { get; set; }

        [JsonPropertyName("localtime")]
        public String? LocalTime { get; set; }
    }


    /*
    "current": {
            "last_updated_epoch": 1686177900,
            "last_updated": "2023-06-08 00:45",
            "temp_c": 18,
            "temp_f": 64.4,
            "is_day": 0,
            "condition": {
                "text": "Moderate rain",
                "icon": "//cdn.weatherapi.com/weather/64x64/night/302.png",
                "code": 1189
            },
            "wind_mph": 2.2,
            "wind_kph": 3.6,
            "wind_degree": 10,
            "wind_dir": "N",
            "pressure_mb": 1008,
            "pressure_in": 29.77,
            "precip_mm": 0.2,
            "precip_in": 0.01,
            "humidity": 100,
            "cloud": 25,
            "feelslike_c": 18,
            "feelslike_f": 64.4,
            "vis_km": 10,
            "vis_miles": 6,
            "uv": 1,
            "gust_mph": 13.9,
            "gust_kph": 22.3
        }
    */
    [SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
        Justification = "Class is instantiated through deserialization.")]
    private sealed class WeatherReport
    {
        [JsonPropertyName("last_updated_epoch")]
        public int LastUpdateTimeEpoch { get; set; } = 0;

        [JsonPropertyName("last_updated")]
        public string LastUpdatedTime { get; set; } = string.Empty;

        [JsonPropertyName("temp_c")]
        public float TempC { get; set; } = -273;

        [JsonPropertyName("temp_f")]
        public float TempF { get; set; } = -273;

        [JsonPropertyName("is_day")]
        public float IsDay { get; set; } = 0;

        [JsonPropertyName("condition")]
        public Condition? Condition { get; set; } = null;

        [JsonPropertyName("wind_mph")]
        public float WindMPH { get; set; } = 0;

        [JsonPropertyName("wind_kph")]
        public float WindKPH { get; set; } = 0;

        [JsonPropertyName("wind_degree")]
        public float WindDegree { get; set; } = 0;

        [JsonPropertyName("wind_dir")]
        public string WindDirection { get; set; } = String.Empty;

        [JsonPropertyName("pressure_mb")]
        public float PressureMillibar { get; set; } = 0;

        [JsonPropertyName("pressure_in")]
        public float PressureInches { get; set; } = 0;

        [JsonPropertyName("precip_mm")]
        public float PrecipMM { get; set; } = 0;

        [JsonPropertyName("precip_in")]
        public float PrecipInches { get; set; } = 0;

        [JsonPropertyName("humidity")]
        public float Humidity { get; set; } = 0;

        [JsonPropertyName("cloud")]
        public float Cloud { get; set; } = 0;

        [JsonPropertyName("feelslike_c")]
        public float FeelsLikeC { get; set; } = 0;

        [JsonPropertyName("feelslike_f")]
        public float FeelsLikeF { get; set; } = 0;

        [JsonPropertyName("vis_km")]
        public float VisibilityKM { get; set; } = 0;

        [JsonPropertyName("vis_miles")]
        public float VisibilityMiles { get; set; } = 0;

        [JsonPropertyName("uv")]
        public float UV { get; set; } = 0;

        [JsonPropertyName("gust_mph")]
        public float GustMPH { get; set; } = 0;

        [JsonPropertyName("gust_kph")]
        public float GustKPH { get; set; } = 0;
    }

    [SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
        Justification = "Class is instantiated through deserialization.")]
    private sealed class Condition
    {
        [JsonPropertyName("text")]
        public string Text { get; set; } = string.Empty;

        [JsonPropertyName("icon")]
        public string Icon { get; set; } = string.Empty;

        [JsonPropertyName("code")]
        public float Code { get; set; } = 0;
    }
}
