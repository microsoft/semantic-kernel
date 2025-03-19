// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.AI;

#pragma warning disable IDE0009 // Use explicit 'this.' qualifier
#pragma warning disable CA2213 // Disposable fields should be disposed
#pragma warning disable IDE0044 // Add readonly modifier

namespace Microsoft.SemanticKernel.ChatCompletion;

// Original source from
// https://raw.githubusercontent.com/dotnet/extensions/main/src/Shared/EmptyCollections/EmptyReadOnlyList.cs

/// <summary>Provides context for an in-flight function invocation.</summary>
public sealed class KernelFunctionInvocationContext
{
    /// <summary>
    /// A nop function used to allow <see cref="Function"/> to be non-nullable. Default instances of
    /// <see cref="KernelFunctionInvocationContext"/> start with this as the target function.
    /// </summary>
    private static readonly AIFunction s_nopFunction = AIFunctionFactory.Create(() => { }, nameof(KernelFunctionInvocationContext));

    /// <summary>The chat contents associated with the operation that initiated this function call request.</summary>
    private IList<ChatMessage> _messages = Array.Empty<ChatMessage>();

    /// <summary>The AI function to be invoked.</summary>
    private AIFunction _function = s_nopFunction;

    /// <summary>The function call content information associated with this invocation.</summary>
    private Microsoft.Extensions.AI.FunctionCallContent _callContent = new(string.Empty, s_nopFunction.Name, EmptyReadOnlyDictionary<string, object?>.Instance);

    /// <summary>Initializes a new instance of the <see cref="KernelFunctionInvocationContext"/> class.</summary>
    internal KernelFunctionInvocationContext()
    {
    }

    /// <summary>Gets or sets the function call content information associated with this invocation.</summary>
    public Microsoft.Extensions.AI.FunctionCallContent CallContent
    {
        get => _callContent;
        set
        {
            Verify.NotNull(value);
            _callContent = value;
        }
    }

    /// <summary>Gets or sets the chat contents associated with the operation that initiated this function call request.</summary>
    public IList<ChatMessage> Messages
    {
        get => _messages;
        set
        {
            Verify.NotNull(value);
            _messages = value;
        }
    }

    /// <summary>Gets or sets the chat options associated with the operation that initiated this function call request.</summary>
    public ChatOptions? Options { get; set; }

    /// <summary>Gets or sets the AI function to be invoked.</summary>
    public AIFunction Function
    {
        get => _function;
        set
        {
            Verify.NotNull(value);
            _function = value;
        }
    }

    /// <summary>Gets or sets the number of this iteration with the underlying client.</summary>
    /// <remarks>
    /// The initial request to the client that passes along the chat contents provided to the <see cref="KernelFunctionInvokingChatClient"/>
    /// is iteration 1. If the client responds with a function call request, the next request to the client is iteration 2, and so on.
    /// </remarks>
    public int Iteration { get; set; }

    /// <summary>Gets or sets the index of the function call within the iteration.</summary>
    /// <remarks>
    /// The response from the underlying client may include multiple function call requests.
    /// This index indicates the position of the function call within the iteration.
    /// </remarks>
    public int FunctionCallIndex { get; set; }

    /// <summary>Gets or sets the total number of function call requests within the iteration.</summary>
    /// <remarks>
    /// The response from the underlying client might include multiple function call requests.
    /// This count indicates how many there were.
    /// </remarks>
    public int FunctionCount { get; set; }

    /// <summary>Gets or sets a value indicating whether to terminate the request.</summary>
    /// <remarks>
    /// In response to a function call request, the function might be invoked, its result added to the chat contents,
    /// and a new request issued to the wrapped client. If this property is set to <see langword="true"/>, that subsequent request
    /// will not be issued and instead the loop immediately terminated rather than continuing until there are no
    /// more function call requests in responses.
    /// </remarks>
    public bool Terminate { get; set; }
}
