// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Transforms;

internal static class DefaultTransforms
{
    public static ValueTask<IEnumerable<ChatMessageContent>> FromInput<TInput>(TInput input, CancellationToken cancellationToken = default)
    {
        if (input is IEnumerable<ChatMessageContent> messages)
        {
            return new ValueTask<IEnumerable<ChatMessageContent>>(messages);
        }

        if (input is ChatMessageContent message)
        {
            return new ValueTask<IEnumerable<ChatMessageContent>>([message]);
        }

        if (input is not string text)
        {
            text = JsonSerializer.Serialize(input);
        }

        return new ValueTask<IEnumerable<ChatMessageContent>>([new ChatMessageContent(AuthorRole.User, text)]);
    }

    public static ValueTask<TOutput> ToOutput<TOutput>(ChatMessageContent result, CancellationToken cancellationToken = default)
    {
        TOutput? output =
            GetDefaultOutput() ??
            GetObjectOutput() ??
            throw new InvalidOperationException($"Unable to transform output message of type {typeof(ChatMessageContent)} to {typeof(TOutput)}.");

        return new ValueTask<TOutput>(output);

        TOutput? GetObjectOutput()
        {
            try
            {
                return JsonSerializer.Deserialize<TOutput>(result.Content ?? string.Empty);
            }
            catch (JsonException)
            {
                return default;
            }
        }

        TOutput? GetDefaultOutput()
        {
            object? output = null;
            if (typeof(ChatMessageContent) == typeof(TOutput))
            {
                output = (object)result;
            }

            if (typeof(string) == typeof(TOutput))
            {
                output = result.Content ?? string.Empty;
            }

            return (TOutput?)output;
        }
    }
}
