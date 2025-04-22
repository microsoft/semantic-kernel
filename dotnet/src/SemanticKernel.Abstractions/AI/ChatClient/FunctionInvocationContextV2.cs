// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

using System;
using System.Collections.Generic;
using Microsoft.Shared.Diagnostics;

namespace Microsoft.Extensions.AI;

/// <summary>Provides context for an in-flight function invocation.</summary>
public partial class FunctionInvocationContextV2
{
    /// <summary>
    /// A nop function used to allow <see cref="Function"/> to be non-nullable. Default instances of
    /// <see cref="FunctionInvocationContext"/> start with this as the target function.
    /// </summary>
    private static readonly AIFunction _nopFunction = AIFunctionFactory.Create(() => { }, nameof(FunctionInvocationContext));

    /// <summary>The chat contents associated with the operation that initiated this function call request.</summary>
    private IList<ChatMessage> _messages = Array.Empty<ChatMessage>();

    /// <summary>The AI function to be invoked.</summary>
    private AIFunction _function = _nopFunction;

    /// <summary>The function call content information associated with this invocation.</summary>
    private FunctionCallContent? _callContent;

    /// <summary>The arguments used with the function.</summary>
    private AIFunctionArgumentsV2? _arguments;

    /// <summary>Initializes a new instance of the <see cref="FunctionInvocationContext"/> class.</summary>
    public FunctionInvocationContextV2()
    {
    }

    /// <summary>Gets or sets the AI function to be invoked.</summary>
    public AIFunction Function
    {
        get => _function;
        set => _function = Throw.IfNull(value);
    }

    /// <summary>Gets or sets the arguments associated with this invocation.</summary>
    public AIFunctionArgumentsV2 Arguments
    {
        get => _arguments ??= [];
        set => _arguments = Throw.IfNull(value);
    }

    /// <summary>Gets or sets the function call content information associated with this invocation.</summary>
    public FunctionCallContent CallContent
    {
        get => _callContent ??= new(string.Empty, _nopFunction.Name, EmptyReadOnlyDictionary<string, object?>.Instance);
        set => _callContent = Throw.IfNull(value);
    }

    /// <summary>Gets or sets the chat contents associated with the operation that initiated this function call request.</summary>
    public IList<ChatMessage> Messages
    {
        get => _messages;
        set => _messages = Throw.IfNull(value);
    }

    /// <summary>Gets or sets the chat options associated with the operation that initiated this function call request.</summary>
    public ChatOptions? Options { get; set; }

    /// <summary>Gets or sets the number of this iteration with the underlying client.</summary>
    /// <remarks>
    /// The initial request to the client that passes along the chat contents provided to the <see cref="FunctionInvokingChatClient"/>
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

    /// <summary>
    /// Gets or sets a value indicating whether the context is happening in a streaming scenario.
    /// </summary>
    public bool IsStreaming { get; set; }
}
