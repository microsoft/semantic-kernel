// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace Step04.Plugins;

/// <summary>
/// Mock plug-in to provide location information.
/// </summary>
internal sealed class LocationPlugin
{
    [KernelFunction]
    [Description("Provide the user's current location by city, region, and country.")]
    public string GetCurrentLocation() => "Bellevue, WA, USA";

    [KernelFunction]
    [Description("Provide the user's home location by city, region, and country.")]
    public string GetHomeLocation() => "Seattle, WA, USA";

    [KernelFunction]
    [Description("Provide the user's work office location by city, region, and country.")]
    public string GetOfficeLocation() => "Redmond, WA, USA";
}
