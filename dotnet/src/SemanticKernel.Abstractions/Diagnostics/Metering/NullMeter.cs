// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Diagnostics.Metering;

/// <summary>
/// Minimalistic meter that does nothing.
/// </summary>
public sealed class NullMeter : IMeter
{
    /// <summary>
    /// Returns the shared instance of <see cref="NullMeter"/>.
    /// </summary>
    public static NullMeter Instance { get; } = new NullMeter();

    /// <inheritdoc />
    public void TrackMetric(string name, double value, IDictionary<string, string>? properties = null)
    {
    }

    #region private ================================================================================

    private NullMeter()
    {
    }

    #endregion
}
