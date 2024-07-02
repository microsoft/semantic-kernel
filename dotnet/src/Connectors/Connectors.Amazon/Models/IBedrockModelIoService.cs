// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models;

public interface IBedrockModelIoService<TRequest, TResponse>
{
    GetInvokeModelRequestBody();
    GetConverseRequestBody();
    InvokeModelRequest GetApiRequestBody(string prompt, PromptExecutionSettings executionSettings);
    TResponse ConvertApiResponse(object response);
}
