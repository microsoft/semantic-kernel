// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Diagnostics.Metering;

public interface IMeter
{
    void TrackMetric(string name, double value, IDictionary<string, string>? properties = null);
}
