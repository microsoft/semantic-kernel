// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models;

public interface IBedrockModelIoService<TRequest, TResponse>
{
    InvokeModelRequest GetApiRequestBody(string prompt, PromptExecutionSettings executionSettings);
    TResponse ConvertApiResponse(object response);
}
