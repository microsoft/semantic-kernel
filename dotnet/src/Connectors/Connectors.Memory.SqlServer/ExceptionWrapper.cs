// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal static class ExceptionWrapper
{
    private const string VectorStoreType = "SqlServer";

    internal static async Task<T> WrapAsync<T>(
        SqlConnection connection,
        SqlCommand command,
        Func<SqlCommand, CancellationToken, Task<T>> func,
        CancellationToken cancellationToken,
        string operationName,
        string? collectionName = null)
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
            throw new VectorStoreOperationException(ex.Message, ex)
            {
                OperationName = operationName,
                VectorStoreType = VectorStoreType,
                CollectionName = collectionName
            };
        }
    }

    internal static async Task<bool> WrapReadAsync(
        SqlDataReader reader,
        CancellationToken cancellationToken,
        string operationName,
        string? collectionName = null)
    {
        try
        {
            return await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            throw new VectorStoreOperationException(ex.Message, ex)
            {
                OperationName = operationName,
                VectorStoreType = VectorStoreType,
                CollectionName = collectionName
            };
        }
    }
}
