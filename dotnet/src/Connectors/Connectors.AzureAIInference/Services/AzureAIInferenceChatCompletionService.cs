// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AzureAIInference;

/// <summary>
/// Initializes a new instance of the <see cref="AzureAIInferenceChatCompletionService"/> class.
/// </summary>
public class AzureAIInferenceChatCompletionService : IChatCompletionService
{
    IReadOnlyDictionary<string, object?> IAIService.Attributes => throw new System.NotImplementedException();

    Task<IReadOnlyList<ChatMessageContent>> IChatCompletionService.GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings, Kernel? kernel, CancellationToken cancellationToken)
    {
        throw new System.NotImplementedException();
    }

    IAsyncEnumerable<StreamingChatMessageContent> IChatCompletionService.GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings, Kernel? kernel, CancellationToken cancellationToken)
    {
        throw new System.NotImplementedException();
    }
}
