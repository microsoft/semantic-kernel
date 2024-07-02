// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models.Mistral;

public class MistralIoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIoService<ITextGenerationRequest, ITextGenerationResponse>
{
    public InvokeModelRequest GetApiRequestBody(string prompt, PromptExecutionSettings settings)
    {
        return new InvokeModelRequest(); //FIX
    }

    public TResponse ConvertApiResponse(object response)
    {
        return response;
    }
}
