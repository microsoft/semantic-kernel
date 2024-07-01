// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
namespace Connectors.Amazon.Core.Responses;

public interface IChatCompletionResponse
{
    IReadOnlyList<ChatMessageContent> GetResults();
}
