// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of CancellationToken
namespace System.Threading;
#pragma warning restore IDE0130

public static class CancellationTokenExtensions
{
    /// <summary>
    /// Combine two cancellation tokens, reusing the given tokens
    /// unless they are both not null/default.
    /// </summary>
    /// <param name="token">Cancellation token 1</param>
    /// <param name="secondToken">Cancellation token 2</param>
    /// <returns>A combination of the two tokens</returns>
    public static CombinedCancellationToken CombineWith(
        this CancellationToken token, CancellationToken secondToken)
    {
        return new CombinedCancellationToken(token, secondToken);
    }
}
