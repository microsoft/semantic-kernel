// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

public static class Example54_AzureChatCompletionWithData
{
    public static async Task RunAsync()
    {
        var chatCompletion = GetChatCompletion();

        var chatHistory = chatCompletion.CreateNewChat();

        chatHistory.AddUserMessage("How did Emily and David meet?");

        string reply = await chatCompletion.GenerateMessageAsync(chatHistory);
    }

    private static AzureChatCompletionWithData GetChatCompletion()
    {
        return new(new AzureChatCompletionWithDataConfig
        {
            CompletionModelId = TestConfiguration.AzureOpenAI.ChatDeploymentName,
            CompletionEndpoint = TestConfiguration.AzureOpenAI.Endpoint,
            CompletionApiKey = TestConfiguration.AzureOpenAI.ApiKey,
            DataSourceEndpoint = TestConfiguration.ACS.Endpoint,
            DataSourceApiKey = TestConfiguration.ACS.ApiKey,
            DataSourceIndex = TestConfiguration.ACS.IndexName
        });
    }
}
