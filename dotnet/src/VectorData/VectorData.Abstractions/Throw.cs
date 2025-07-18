// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

internal static class Throw
{
    /// <summary>Throws an exception indicating that a required service is not available.</summary>
    public static InvalidOperationException CreateMissingServiceException(Type serviceType, object? serviceKey) =>
        new(serviceKey is null ?
            $"No service of type '{serviceType}' is available." :
            $"No service of type '{serviceType}' for the key '{serviceKey}' is available.");
}
