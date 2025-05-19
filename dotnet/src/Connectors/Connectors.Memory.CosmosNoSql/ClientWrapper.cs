// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using Microsoft.Azure.Cosmos;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

internal sealed class ClientWrapper : IDisposable
{
    private readonly bool _ownsClient;
    private int _referenceCount = 1;

    internal ClientWrapper(CosmosClient cosmosClient, bool ownsClient)
    {
        this.Client = cosmosClient;
        this._ownsClient = ownsClient;
    }

    internal CosmosClient Client { get; }

    internal ClientWrapper Share()
    {
        if (this._ownsClient)
        {
            Interlocked.Increment(ref this._referenceCount);
        }

        return this;
    }

    public void Dispose()
    {
        if (this._ownsClient)
        {
            if (Interlocked.Decrement(ref this._referenceCount) == 0)
            {
                this.Client.Dispose();
            }
        }
    }
}
