// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.AotTests.Plugins;

internal sealed class Location
{
    public string Country { get; set; }

    public string City { get; set; }

    public Location(string country, string city)
    {
        this.Country = country;
        this.City = city;
    }
}
