// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Options for the <see cref="ContextualFunctionProvider"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class ContextualFunctionProviderOptions
{
    /// <summary>
    /// The number of recent messages(messages from previous model/agent invocations) the provider uses to form a context.
    /// The provider collects all messages from all model/agent invocations, up to this number,
    /// and prepends them to the new messages of the current model/agent invocation to build a context.
    /// While collecting new messages, the provider will remove the oldest messages
    /// to keep the number of recent messages within the specified limit.
    /// </summary>
    /// <remarks>
    /// Using the recent messages together with the new messages can be very useful
    /// in cases where the model/agent is prompted to perform a task that requires details from
    /// previous invocation(s). For example, if the agent is asked to provision an Azure resource in the first
    /// invocation and deploy the resource in the second invocation, the second invocation will need
    /// information about the provisioned resource in the first invocation to deploy it.
    /// </remarks>
    public int NumberOfRecentMessagesInContext { get; set; } = 2;

    /// <summary>
    /// A callback function that returns a value used to create a context embedding. The value is vectorized,
    /// and the resulting vector is used to perform vector searches for functions relevant to the context.
    /// If not provided, the default behavior is to concatenate the non-empty messages into a single string,
    /// separated by a new line.
    /// </summary>
    /// <remarks>
    /// The callback receives three parameters:
    /// `recentMessages` - messages from the previous model/agent invocations.
    /// `newMessages` - the new messages of the current model/agent invocation.
    /// `cancellationToken` - a cancellation token that can be used to cancel the operation.
    /// </remarks>
    public Func<IEnumerable<ChatMessage>, IEnumerable<ChatMessage>, CancellationToken, Task<string>>? ContextEmbeddingValueProvider { get; set; }

    /// <summary>
    /// A callback function that returns a value used to create a function embedding. The value is vectorized,
    /// and the resulting vector is stored in the vector store for use in vector searches for functions relevant
    /// to the context.
    /// If not provided, the default behavior is to concatenate the function name and description into a single string.
    /// </summary>
    /// <remarks>
    /// The callback receives two parameters:
    /// `function` - the function to get embedding value for.
    /// `cancellationToken` - a cancellation token that can be used to cancel the operation.
    /// </remarks>
    public Func<AIFunction, CancellationToken, Task<string>>? EmbeddingValueProvider { get; set; }
}
