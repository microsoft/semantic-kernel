// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Contains helper methods for mapping fields to and from the format required by the Redis client sdk.
/// </summary>
internal static class RedisVectorStoreRecordFieldMapping
{
    /// <summary>
    /// Convert a vector to a byte array as required by the Redis client sdk when using hashsets.
    /// </summary>
    /// <param name="vector">The vector to convert.</param>
    /// <returns>The byte array.</returns>
    public static byte[] ConvertVectorToBytes(ReadOnlyMemory<float> vector)
    {
        return MemoryMarshal.AsBytes(vector.Span).ToArray();
    }

    /// <summary>
    /// Convert a vector to a byte array as required by the Redis client sdk when using hashsets.
    /// </summary>
    /// <param name="vector">The vector to convert.</param>
    /// <returns>The byte array.</returns>
    public static byte[] ConvertVectorToBytes(ReadOnlyMemory<double> vector)
    {
        return MemoryMarshal.AsBytes(vector.Span).ToArray();
    }
}
