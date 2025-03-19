// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents a response from an agent invocation.
/// </summary>
/// <typeparam name="T">The type of data returned by the response.</typeparam>
public class AgentInvokeResponseAsyncEnumerable<T> : IAgentInvokeResponseAsyncEnumerable<T>
{
    private readonly IAsyncEnumerable<T> _asyncEnumerable;
    private readonly AgentThread _thread;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentInvokeResponseAsyncEnumerable{T}"/> class.
    /// </summary>
    /// <param name="asyncEnumerable">The internal <see cref="IAsyncEnumerable{T}"/> that will be combined with additional invoke specific response information.</param>
    /// <param name="thread">The conversation thread associated with the response.</param>
    public AgentInvokeResponseAsyncEnumerable(IAsyncEnumerable<T> asyncEnumerable, AgentThread thread)
    {
        Verify.NotNull(asyncEnumerable);
        Verify.NotNull(thread);

        this._asyncEnumerable = asyncEnumerable;
        this._thread = thread;
    }

    /// <inheritdoc/>
    public AgentThread Thread => this._thread;

    /// <inheritdoc/>
    public IAsyncEnumerator<T> GetAsyncEnumerator(CancellationToken cancellationToken = default)
    {
        return this._asyncEnumerable.GetAsyncEnumerator(cancellationToken);
    }
}
