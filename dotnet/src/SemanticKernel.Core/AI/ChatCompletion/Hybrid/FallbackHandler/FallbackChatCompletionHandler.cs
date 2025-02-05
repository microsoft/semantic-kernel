// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// A hybrid chat client policy that delegates chat completion to the first available client.
/// </summary>
public sealed class FallbackChatCompletionHandler : ChatCompletionHandler
{
    public FallbackEvaluator FallbackEvaluator { get; set; } = new DefaultFallbackEvaluator();

    public override async Task<Extensions.AI.ChatCompletion> CompleteAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default)
    {
        for (int i = 0; i < context.ChatClients.Count; i++)
        {
            var chatClient = context.ChatClients.ElementAt(i).Key;

            try
            {
                return await chatClient.CompleteAsync(context.ChatMessages, context.Options, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                if (this.ShouldFallbackToNextClient(ex, i, context.ChatClients.Count))
                {
                    continue;
                }

                throw;
            }
        }

        throw new InvalidOperationException("No client provided for chat completion.");
    }

    public override async IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(ChatCompletionHandlerContext context, CancellationToken cancellationToken = default)
    {
        if (context.ChatClients.Count == 0)
        {
            throw new InvalidOperationException("No client provided for chat completion.");
        }

        for (int i = 0; i < context.ChatClients.Count; i++)
        {
            var chatClient = context.ChatClients.ElementAt(i).Key;

            IAsyncEnumerable<StreamingChatCompletionUpdate> completionStream = chatClient.CompleteStreamingAsync(context.ChatMessages, context.Options, cancellationToken);

            ConfiguredCancelableAsyncEnumerable<StreamingChatCompletionUpdate>.Enumerator enumerator = completionStream.ConfigureAwait(false).GetAsyncEnumerator();

            try
            {
                try
                {
                    // Move to the first update to reveal any exceptions.
                    if (!await enumerator.MoveNextAsync())
                    {
                        yield break;
                    }
                }
                catch (Exception ex)
                {
                    if (this.ShouldFallbackToNextClient(ex, i, context.ChatClients.Count))
                    {
                        continue;
                    }

                    throw;
                }

                // Yield the first update.
                yield return enumerator.Current;

                // Yield the rest of the updates.
                while (await enumerator.MoveNextAsync())
                {
                    yield return enumerator.Current;
                }

                // The stream has ended so break the while loop.
                break;
            }
            finally
            {
                await enumerator.DisposeAsync();
            }
        }
    }

    private bool ShouldFallbackToNextClient(Exception ex, int clientIndex, int numberOfClients)
    {
        // If the exception is thrown by the last client then don't fallback.
        if (clientIndex == numberOfClients - 1)
        {
            return false;
        }

        return this.FallbackEvaluator.ShouldFallbackToNextClient(new() { Exception = ex });
    }
}
