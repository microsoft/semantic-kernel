// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

#pragma warning disable CA1068 // CancellationToken parameters must come last

internal static class ExceptionWrapper
{
    internal static async Task<T> WrapAsync<T>(
        SqlConnection connection,
        SqlCommand command,
        Func<SqlCommand, CancellationToken, Task<T>> func,
        string operationName,
        string? vectorStoreName = null,
        string? collectionName = null,
        CancellationToken cancellationToken = default)
    {
        if (connection.State != System.Data.ConnectionState.Open)
        {
            await connection.OpenAsync(cancellationToken).ConfigureAwait(false);
        }

        try
        {
            return await func(command, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
#if NET
            await connection.DisposeAsync().ConfigureAwait(false);
#else
            connection.Dispose();
#endif

            throw new VectorStoreOperationException(ex.Message, ex)
            {
                VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
                VectorStoreName = vectorStoreName,
                CollectionName = collectionName,
                OperationName = operationName
            };
        }
    }

    internal static async Task<bool> WrapReadAsync(
        SqlDataReader reader,
        string operationName,
        string? vectorStoreName = null,
        string? collectionName = null,
        CancellationToken cancellationToken = default)
    {
        try
        {
            return await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            throw new VectorStoreOperationException(ex.Message, ex)
            {
                VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
                VectorStoreName = vectorStoreName,
                CollectionName = collectionName,
                OperationName = operationName
            };
        }
    }
}
