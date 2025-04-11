// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains helpers for reading vector store model properties and their attributes.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class VectorStoreErrorHandler
{
    /// <summary>
    /// Run the given model conversion and wrap any exceptions with <see cref="VectorStoreRecordMappingException"/>.
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="vectorStoreSystemName">The name of the vector store system the operation is being run on.</param>
    /// <param name="vectorStoreName">The name of the vector store the operation is being run on.</param>
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static T RunModelConversion<T>(
        string vectorStoreSystemName,
        string? vectorStoreName,
        string collectionName,
        string operationName,
        Func<T> operation)
    {
        try
        {
            return operation.Invoke();
        }
        catch (Exception ex)
        {
            throw new VectorStoreRecordMappingException("Failed to convert vector store record.", ex)
            {
                VectorStoreSystemName = vectorStoreSystemName,
                VectorStoreName = vectorStoreName,
                CollectionName = collectionName,
                OperationName = operationName
            };
        }
    }
}
