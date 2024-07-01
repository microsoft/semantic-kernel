// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
namespace Connectors.Amazon.Core.Requests;

// public interface IChatCompletionRequest
// {
//     ChatHistory ChatHistory { get; }
//     PromptExecutionSettings? ExecutionSettings { get; }
// }

public interface IChatCompletionRequest
{
    string InputText { get; }

    double? TopP { get; }

    double? Temperature { get; }

    int? MaxTokens { get; }

    IList<string>? StopSequences { get; }
}
