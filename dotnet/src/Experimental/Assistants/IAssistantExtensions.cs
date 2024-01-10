// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Convenience actions for <see cref="IAssistant"/>.
/// </summary>
public static class IAssistantExtensions
{
    /// <summary>
    /// Invoke assistant with user input
    /// </summary>
    /// <param name="assistant">the assistant</param>
    /// <param name="input">the user input</param>
    /// <param name="cancellationToken">a cancel token</param>
    /// <returns>chat messages</returns>
    public static async IAsyncEnumerable<IChatMessage> InvokeAsync(
        this IAssistant assistant,
        string input,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IChatThread thread = await assistant.NewThreadAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            await foreach (var message in thread.InvokeAsync(assistant, input, cancellationToken))
            {
                yield return message;
            }
        }
        finally
        {
            await thread.DeleteAsync(cancellationToken).ConfigureAwait(false);
        }
    }
}
