// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// A reference-counting wrapper around an <see cref="NpgsqlDataSource"/> instance.
/// </summary>
internal sealed class NpgsqlDataSourceArc(NpgsqlDataSource dataSource) : IDisposable
{
    private int _referenceCount = 1;

    public void Dispose()
    {
        if (Interlocked.Decrement(ref this._referenceCount) == 0)
        {
            dataSource.Dispose();
        }
    }

    internal NpgsqlDataSourceArc IncrementReferenceCount()
    {
        Interlocked.Increment(ref this._referenceCount);

        return this;
    }
}
