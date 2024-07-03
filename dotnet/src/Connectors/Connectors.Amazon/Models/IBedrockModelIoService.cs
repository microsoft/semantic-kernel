// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models;

public interface IBedrockModelIoService<TRequest, TResponse>
{
    ITextGenerationRequest GetInvokeModelRequestBody(string text, PromptExecutionSettings settings);
    object GetConverseRequestBody();
}
