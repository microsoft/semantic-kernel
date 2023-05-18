// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;

namespace Microsoft.SemanticKernel.Orchestration;

public class CombinedCancellationToken : IDisposable
{
    private readonly CancellationTokenSource? _cts = null;

    /// <summary>
    /// Cancellation token to observe both the given tokens
    /// </summary>
    public CancellationToken Token { get; private set; }

    /// <summary>
    /// Create a new instance, wrapping two cancellation tokens.
    /// </summary>
    /// <param name="token1">Token 1</param>
    /// <param name="token2">Token 2</param>
    public CombinedCancellationToken(CancellationToken token1, CancellationToken token2)
    {
        // If the first token is empty, there is no need to create a new source
        // and we can reuse the second token. Same if the second token is empty
        // or the tokens are the same.
        if (token1 == default)
        {
            this.Token = token2;
        }
        else if (token2 == default || token1.Equals(token2))
        {
            this.Token = token1;
        }
        else
        {
            // Create a new resource only when both tokens are not empty
            this._cts = CancellationTokenSource.CreateLinkedTokenSource(token1, token2);
            this.Token = this._cts.Token;
        }
    }

    /// <inheritdoc />
    public void Dispose()
    {
        this._cts?.Dispose();
    }
}
