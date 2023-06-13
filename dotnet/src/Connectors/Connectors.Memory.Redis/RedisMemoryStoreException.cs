// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Memory.Redis;

#pragma warning disable RCS1194 // Implement exception constructors

/// <summary>
/// Exception thrown by the Redis connector
/// </summary>
public class RedisMemoryStoreException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="RedisMemoryStoreException"/> class.
    /// </summary>
    /// <param name="message">Exception message.</param>
    internal RedisMemoryStoreException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisMemoryStoreException"/> class.
    /// </summary>
    /// <param name="message">Exception message.</param>
    /// <param name="innerException">Inner exception.</param>
    internal RedisMemoryStoreException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
