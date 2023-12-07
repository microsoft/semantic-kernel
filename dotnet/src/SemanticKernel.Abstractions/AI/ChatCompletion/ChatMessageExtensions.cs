// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Extension methods for <see cref="ChatMessage"/> class.
/// </summary>
public static class ChatMessageExtensions
{
    /// <summary>
    /// Returns chat message content
    /// </summary>
    /// <typeparam name="T">Target type for result value casting.</typeparam>
    /// <exception cref="InvalidCastException">Thrown when it's not possible to cast result value to <typeparamref name="T"/>.</exception>
    public static T? GetContent<T>(this ChatMessage message)
    {
        if (message?.Content is null)
        {
            return default;
        }

        if (message.Content is T typedResult)
        {
            return typedResult;
        }

        throw new InvalidCastException($"Cannot cast {message.Content.GetType()} to {typeof(T)}");
    }
}
