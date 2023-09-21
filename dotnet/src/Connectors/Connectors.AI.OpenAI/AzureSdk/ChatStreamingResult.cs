// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Diagnostics;
using Orchestration;
using SemanticKernel.AI.ChatCompletion;
using SemanticKernel.AI.TextCompletion;
using static FunctionCalling.Extensions.ChatMessageExtensions;


internal sealed class ChatStreamingResult : IChatStreamingResult, ITextStreamingResult
{
    private readonly ModelResult _modelResult;
    private readonly StreamingChatChoice _choice;
    private readonly bool _isFunctionCall;


    public ChatStreamingResult(StreamingChatCompletions resultData, StreamingChatChoice choice, bool isFunctionCall = false)
    {
        Verify.NotNull(choice);
        _choice = choice;
        _modelResult = new ModelResult(resultData);
        _isFunctionCall = isFunctionCall;
    }


    public ModelResult ModelResult => _modelResult;


    /// <inheritdoc/>
    public async Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        var chatMessage = await _choice.GetMessageStreaming(cancellationToken)
            .LastOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);

        if (chatMessage is null)
        {
            throw new SKException("Unable to get chat message from stream");
        }

        if (!_isFunctionCall)
        {
            return new SKChatMessage(chatMessage);
        }

        var content = chatMessage.FunctionCall.Arguments;
        var functionName = chatMessage.FunctionCall.Name;

        if (IsValidJson(content))
        {
            return new SKChatMessage(AuthorRole.FunctionCall.Label, content, functionName);
        }

        content = CleanJson(content);

        Console.WriteLine($"Cleaned Json for Function {chatMessage.FunctionCall.Name}: \n" +
                          $"Original Version: {chatMessage.FunctionCall.Arguments} \n" +
                          $"Cleaned Version: {content}");

        return new SKChatMessage(AuthorRole.FunctionCall.Label, content, functionName);
    }


    /// <inheritdoc/>
    public async IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var message in _choice.GetMessageStreaming(cancellationToken))
        {
            if (!_isFunctionCall)
            {
              if (!string.IsNullOrWhiteSpace(message.Content))
              {
                yield return new SKChatMessage(message);
              }
              
                continue;
            }

            var content = message.FunctionCall.Arguments;
            var functionName = message.FunctionCall.Name;

            // if the contents first character is not a curly brace, then clean the json
            if (IsValidJson(content))
            {
                yield return new SKChatMessage(AuthorRole.FunctionCall.Label, content, functionName);

                continue;
            }

            content = CleanJson(content);
            Console.WriteLine($"Cleaned Json for Function {message.FunctionCall.Name}: \n" +
                              $"Original Version: {message.FunctionCall.Arguments} \n" +
                              $"Cleaned Version: {content}");

            yield return new SKChatMessage(AuthorRole.FunctionCall.Label, content, functionName);
           
        }
    }


    /// <inheritdoc/>
    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default) => (await GetChatMessageAsync(cancellationToken).ConfigureAwait(false)).Content;


    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var result in GetStreamingChatMessageAsync(cancellationToken).ConfigureAwait(false))
        {
            if (!string.IsNullOrWhiteSpace(result.Content))
            {
                yield return result.Content;
            }
        }
    }
}
