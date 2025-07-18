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
#if !NETCOREAPP
        return TransformInput().AsValueTask();
#else
        return ValueTask.FromResult(TransformInput());
#endif

        IEnumerable<ChatMessageContent> TransformInput() =>
            input switch
            {
                IEnumerable<ChatMessageContent> messages => messages,
                ChatMessageContent message => [message],
                string text => [new ChatMessageContent(AuthorRole.User, text)],
                _ => [new ChatMessageContent(AuthorRole.User, JsonSerializer.Serialize(input))]
            };
    }

    public static ValueTask<TOutput> ToOutput<TOutput>(IList<ChatMessageContent> result, CancellationToken cancellationToken = default)
    {
        bool isSingleResult = result.Count == 1;

        TOutput output =
            GetDefaultOutput() ??
            GetObjectOutput() ??
            throw new InvalidOperationException($"Unable to transform output to {typeof(TOutput)}.");

        return new ValueTask<TOutput>(output);

        TOutput? GetObjectOutput()
        {
            if (!isSingleResult)
            {
                return default;
            }

            try
            {
                return JsonSerializer.Deserialize<TOutput>(result[0].Content ?? string.Empty);
            }
            catch (JsonException)
            {
                return default;
            }
        }

        TOutput? GetDefaultOutput()
        {
            object? output = null;
            if (typeof(TOutput).IsAssignableFrom(result.GetType()))
            {
                output = (object)result;
            }
            else if (isSingleResult && typeof(ChatMessageContent).IsAssignableFrom(typeof(TOutput)))
            {
                output = (object)result[0];
            }
            else if (isSingleResult && typeof(string) == typeof(TOutput))
            {
                output = result[0].Content ?? string.Empty;
            }

            return (TOutput?)output;
        }
    }
}
