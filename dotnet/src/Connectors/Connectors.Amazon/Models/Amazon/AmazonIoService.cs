// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.Extensions.Azure;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models.Amazon;

public class AmazonIoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIoService<ITextGenerationRequest, ITextGenerationResponse>
{
    public ITextGenerationRequest GetInvokeModelRequestBody(string prompt, PromptExecutionSettings executionSettings)
    {
        var textGenerationConfig = new TitanRequest.TitanTextGenerationRequest
        {
            InputText = prompt,
            TextGenerationConfig = new TitanRequest.AmazonTitanTextGenerationConfig
            {
                Temperature = (double)executionSettings.ExtensionData?["temperature"],
                TopP = (double)executionSettings.ExtensionData?["topP"],
                MaxTokenCount = (int)executionSettings.ExtensionData?["maxTokenCount"],
                StopSequences = (IList<string>)executionSettings.ExtensionData?["stopSequences"]
            }
        };
        if (executionSettings.ExtensionData == null)
        {
            executionSettings.ExtensionData = new Dictionary<string, object>();
        }
        executionSettings.ExtensionData["textGenerationConfig"] = textGenerationConfig.TextGenerationConfig;

        return textGenerationConfig;
    }
    public object GetConverseRequestBody()
    {
        throw new NotImplementedException();
    }
}
