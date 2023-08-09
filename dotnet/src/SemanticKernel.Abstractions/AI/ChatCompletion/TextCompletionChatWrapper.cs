// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;
public class TextCompletionChatWrapper : IChatCompletion, ITextCompletion
{
    private readonly ITextCompletion _wrappedCompletion;
    private readonly IChatToTextConverter _converter;

    public TextCompletionChatWrapper(ITextCompletion wrappedCompletion, IChatToTextConverter? converter = null)
    {
        this._wrappedCompletion = wrappedCompletion;
        this._converter = converter ?? new ChatToTextConverter();
    }

    public ChatHistory CreateNewChat(string? instructions = null)
    {
        var chatHistory = new ChatHistory();
        if (!string.IsNullOrWhiteSpace(instructions))
        {
            // TODO reconcile ChatHistory with OpenAiChatHistory, why is there a different class?
            chatHistory.AddSystemMessage(instructions);
        }
        return chatHistory;
    }

    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(ChatHistory chat, ChatRequestSettings? chatRequestSettings = null, CancellationToken cancellationToken = default)
    {
        var text = this._converter.ChatToText(chat);
        var completionSettings = this._converter.ChatSettingsToCompleteSettings(chatRequestSettings);

        var result = await this._wrappedCompletion.GetCompletionsAsync(text, completionSettings, cancellationToken).ConfigureAwait(false);

        return this._converter.TextResultToChatResult(result);
    }

    public IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(ChatHistory chat, ChatRequestSettings? chatRequestSettings = null, CancellationToken cancellationToken = default)
    {
        var text = this._converter.ChatToText(chat);
        var completionSettings = this._converter.ChatSettingsToCompleteSettings(chatRequestSettings);

        var response = this._wrappedCompletion.GetStreamingCompletionsAsync(text, completionSettings, cancellationToken);

        return this._converter.TextResultToChatResult(response);
    }

    public Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        return this._wrappedCompletion.GetCompletionsAsync(text, requestSettings, cancellationToken);
    }

    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        return this._wrappedCompletion.GetStreamingCompletionsAsync(text, requestSettings, cancellationToken);
    }
}
