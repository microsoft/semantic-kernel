// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models.Amazon;

public class AmazonIoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIoService<ITextGenerationRequest, ITextGenerationResponse>
{
    public InvokeModelRequest GetApiRequestBody(string prompt, PromptExecutionSettings settings)
    {
        return new InvokeModelRequest(); //FIX
        // Convert prompt and PromptExecutionSettings to the Titan-specific request structure
        // return new TitanRequest.TitanChatCompletionRequest()
        // {
        //     InputText = prompt,
        //     TextGenerationConfig = new TitanRequest.AmazonTitanTextGenerationConfig
        //     {
        //         TopP = settings.TopP == 0 ? null : settings.TopP,
        //         Temperature = settings.Temperature,
        //         MaxTokenCount = settings.MaxTokens,
        //         StopSequences = settings.StopSequences
        //     }
        // };
    }

    public TResponse ConvertApiResponse(object response)
    {
        // Convert the Titan-specific response to IReadOnlyList<ChatmsgContent>
        // return (TitanResponse)response;
        return response;
        // return titanResponse?.GetResults() ?? new List<ChatMessageContent>();
        // return titanResponse.Results.Select(result => new TextContent(result.OutputText)).ToList();
    }
}
