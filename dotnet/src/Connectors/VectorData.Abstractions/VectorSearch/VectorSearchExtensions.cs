// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides a collection of static methods for extending <see cref="IVectorizedSearch{TRecord}"/> instances.</summary>
public static class VectorSearchExtensions
{
    /// <summary>
    /// Asks the <see cref="IVectorSearch{TRecord}"/> for an object of the specified type <paramref name="serviceType"/>
    /// and throw an exception if one isn't available.
    /// </summary>
    /// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
    /// <param name="vectorSearch">The vector search.</param>
    /// <param name="serviceType">The type of object being requested.</param>
    /// <param name="serviceKey">An optional key that can be used to help identify the target service.</param>
    /// <returns>The found object.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="vectorSearch"/> is <see langword="null"/>.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="serviceType"/> is <see langword="null"/>.</exception>
    /// <exception cref="InvalidOperationException">No service of the requested type for the specified key is available.</exception>
    public static object GetRequiredService<TRecord>(this IVectorSearch<TRecord> vectorSearch, Type serviceType, object? serviceKey = null)
    {
        if (vectorSearch is null) { throw new ArgumentNullException(nameof(vectorSearch)); }
        if (serviceType is null) { throw new ArgumentNullException(nameof(serviceType)); }

        return
            vectorSearch.GetService(serviceType, serviceKey) ??
            throw Throw.CreateMissingServiceException(serviceType, serviceKey);
    }
}
