// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.ApplicationInsights;
using Microsoft.SemanticKernel.Diagnostics.Metering;

/// <summary>
/// Example of <see cref="IMeter"/> implementation to be used with Application Insights.
/// </summary>
internal sealed class ApplicationInsightsMeter : IMeter
{
    private readonly TelemetryClient _telemetryClient;

    public ApplicationInsightsMeter(TelemetryClient telemetryClient)
    {
        this._telemetryClient = telemetryClient;
    }

    public void TrackMetric(string name, double value, IDictionary<string, string>? properties = null)
    {
        // TrackMetric here is used for demonstration purposes. It's not preferred method for sending metrics. 
        // GetMetric.TrackValue should be used instead.
        // More information here: https://learn.microsoft.com/en-us/azure/azure-monitor/app/api-custom-events-metrics#trackmetric
        this._telemetryClient.TrackMetric(name, value, properties);
    }
}
