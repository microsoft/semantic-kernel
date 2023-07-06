// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Diagnostics.Metering;

/// <summary>
/// Represents a type used to perform metering.
/// </summary>
public interface IMeter
{
    /// <summary>
    /// Captures metric value for given metric name.
    /// </summary>
    /// <param name="name">Metric name.</param>
    /// <param name="value">Metric value.</param>
    /// <param name="properties">Optional metric properties.</param>
    void TrackMetric(string name, double value, IDictionary<string, string>? properties = null);
}
