// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Mistral;

public class MistralIoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIoService<ITextGenerationRequest, ITextGenerationResponse>
{
    public ITextGenerationRequest GetInvokeModelRequestBody(string prompt, PromptExecutionSettings executionSettings)
    {
        throw new NotImplementedException();
    }

    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory)
    {
        throw new NotImplementedException();
    }
}
