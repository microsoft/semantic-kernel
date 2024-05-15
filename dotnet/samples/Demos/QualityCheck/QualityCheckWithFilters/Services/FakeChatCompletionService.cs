// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;

namespace QualityCheckWithFilters.Services;

#pragma warning disable CS1998

/// <summary>
/// Fake chat completion service to simulate a call to LLM and return predefined result for demonstration purposes.
/// </summary>
internal sealed class FakeChatCompletionService(string modelId, string result) : IChatCompletionService
{
    public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?> { [AIServiceExtensions.ModelIdKey] = modelId };

    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult<IReadOnlyList<ChatMessageContent>>([new(AuthorRole.Assistant, result)]);
    }

    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        yield return new StreamingChatMessageContent(AuthorRole.Assistant, result);
    }
}
