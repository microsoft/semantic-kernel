// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models.Amazon;

public class AmazonIoService : IBedrockModelIoService<TitanRequest, TitanResponse>
{
    public IChatCompletionRequest GetApiRequestBody(string prompt, IChatCompletionRequest settings)
    {
        // Convert prompt and PromptExecutionSettings to the Titan-specific request structure
        return new TitanRequest.TitanChatCompletionRequest()
        {
            InputText = prompt,
            TextGenerationConfig = new TitanRequest.AmazonTitanTextGenerationConfig
            {
                TopP = settings.TopP == 0 ? null : settings.TopP,
                Temperature = settings.Temperature,
                MaxTokenCount = settings.MaxTokens,
                StopSequences = settings.StopSequences
            }
        };
    }

    public TitanResponse ConvertApiResponse(object response)
    {
        // Convert the Titan-specific response to IReadOnlyList<ChatmsgContent>
        return (TitanResponse)response;
        // return titanResponse?.GetResults() ?? new List<ChatMessageContent>();
        // return titanResponse.Results.Select(result => new TextContent(result.OutputText)).ToList();
    }
}
