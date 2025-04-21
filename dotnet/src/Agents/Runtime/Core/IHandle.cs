// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core;

/// <summary>
/// Defines a handler interface for processing items of type <typeparamref name="T"/>.
/// </summary>
/// <typeparam name="T">The type of item to be handled.</typeparam>
public interface IHandle<in T>
{
    /// <summary>
    /// Handles the specified item asynchronously.
    /// </summary>
    /// <param name="item">The item to be handled.</param>
    /// <param name="messageContext">The context of the message being handled.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    ValueTask HandleAsync(T item, MessageContext messageContext);
}

/// <summary>
/// Defines a handler interface for processing items of type <typeparamref name="TIn"/> and <typeparamref name="TOut"/>.
/// </summary>
/// <typeparam name="TIn">The input type</typeparam>
/// <typeparam name="TOut">The output type</typeparam>
public interface IHandle<in TIn, TOut>
{
    /// <summary>
    /// Handles the specified item asynchronously.
    /// </summary>
    /// <param name="item">The item to be handled.</param>
    /// <param name="messageContext">The context of the message being handled.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    ValueTask<TOut> HandleAsync(TIn item, MessageContext messageContext);
}
