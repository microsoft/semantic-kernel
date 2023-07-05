// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.ApplicationInsights;
using Microsoft.SemanticKernel.Diagnostics.Metering;

/// <summary>
/// Example of <see cref="IMeter"/> implementation to be used with Application Insights.
/// </summary>
internal class ApplicationInsightsMeter : IMeter
{
    private readonly TelemetryClient _telemetryClient;

    public ApplicationInsightsMeter(TelemetryClient telemetryClient)
    {
        this._telemetryClient = telemetryClient;
    }

    public void TrackMetric(string name, double value, IDictionary<string, string>? properties = null)
    {
        this._telemetryClient.TrackMetric(name, value, properties);
    }
}
