﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides a collection of static methods for extending <see cref="IVectorizableTextSearch{TRecord}"/> instances.</summary>
[Experimental("MEVD9000")]
public static class VectorizableTextSearchExtensions
{
    /// <summary>
    /// Asks the <see cref="IVectorizableTextSearch{TRecord}"/> for an object of the specified type <paramref name="serviceType"/>
    /// and throw an exception if one isn't available.
    /// </summary>
    /// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
    /// <param name="vectorizableTextSearch">The vectorizable text search.</param>
    /// <param name="serviceType">The type of object being requested.</param>
    /// <param name="serviceKey">An optional key that can be used to help identify the target service.</param>
    /// <returns>The found object.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="vectorizableTextSearch"/> is <see langword="null"/>.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="serviceType"/> is <see langword="null"/>.</exception>
    /// <exception cref="InvalidOperationException">No service of the requested type for the specified key is available.</exception>
    public static object GetRequiredService<TRecord>(this IVectorizableTextSearch<TRecord> vectorizableTextSearch, Type serviceType, object? serviceKey = null)
    {
        if (vectorizableTextSearch is null) { throw new ArgumentNullException(nameof(vectorizableTextSearch)); }
        if (serviceType is null) { throw new ArgumentNullException(nameof(serviceType)); }

        return
            vectorizableTextSearch.GetService(serviceType, serviceKey) ??
            throw Throw.CreateMissingServiceException(serviceType, serviceKey);
    }
}
