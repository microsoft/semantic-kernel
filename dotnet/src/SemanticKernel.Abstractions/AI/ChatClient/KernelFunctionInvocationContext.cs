// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using Microsoft.Extensions.AI;

#pragma warning disable IDE0009 // Use explicit 'this.' qualifier
#pragma warning disable CA2213 // Disposable fields should be disposed
#pragma warning disable IDE0044 // Add readonly modifier

namespace Microsoft.SemanticKernel.ChatCompletion;

// Slight modified source from
// https://raw.githubusercontent.com/dotnet/extensions/refs/heads/main/src/Libraries/Microsoft.Extensions.AI/ChatCompletion/FunctionInvocationContext.cs

/// <summary>Provides context for an in-flight function invocation.</summary>
[ExcludeFromCodeCoverage]
internal class KernelFunctionInvocationContext
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
    private Microsoft.Extensions.AI.FunctionCallContent? _callContent;

    /// <summary>The arguments used with the function.</summary>
    private AIFunctionArguments? _arguments;

    /// <summary>Initializes a new instance of the <see cref="FunctionInvocationContext"/> class.</summary>
    public KernelFunctionInvocationContext()
    {
    }

    /// <summary>Gets or sets the AI function to be invoked.</summary>
    public AIFunction Function
    {
        get => _function;
        set => _function = Throw.IfNull(value);
    }

    /// <summary>Gets or sets the arguments associated with this invocation.</summary>
    public AIFunctionArguments Arguments
    {
        get => _arguments ??= [];
        set => _arguments = Throw.IfNull(value);
    }

    /// <summary>Gets or sets the function call content information associated with this invocation.</summary>
    public Microsoft.Extensions.AI.FunctionCallContent CallContent
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

    private static class Throw
    {
        /// <summary>
        /// Throws an <see cref="System.ArgumentNullException"/> if the specified argument is <see langword="null"/>.
        /// </summary>
        /// <typeparam name="T">Argument type to be checked for <see langword="null"/>.</typeparam>
        /// <param name="argument">Object to be checked for <see langword="null"/>.</param>
        /// <param name="paramName">The name of the parameter being checked.</param>
        /// <returns>The original value of <paramref name="argument"/>.</returns>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        [return: NotNull]
        public static T IfNull<T>([NotNull] T argument, [CallerArgumentExpression(nameof(argument))] string paramName = "")
        {
            if (argument is null)
            {
                throw new ArgumentNullException(paramName);
            }

            return argument;
        }
    }
}
