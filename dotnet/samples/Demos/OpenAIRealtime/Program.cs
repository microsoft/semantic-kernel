// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Configuration;
using OpenAI.RealtimeConversation;

namespace OpenAIRealtime;

#pragma warning disable OPENAI002

internal class Program
{
    public static void Main(string[] args)
    {
        Console.WriteLine("Hello, World!");
    }

    #region Configuration

    private static RealtimeConversationClient GetRealtimeConversationClient()
    {
        // Get configuration
        var config = new ConfigurationBuilder()
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build();

        var openAIOptions = config.GetSection(OpenAIOptions.SectionName).Get<OpenAIOptions>();
        var azureOpenAIOptions = config.GetSection(AzureOpenAIOptions.SectionName).Get<AzureOpenAIOptions>();

        if (openAIOptions is not null && openAIOptions.IsValid)
        {
            return new RealtimeConversationClient(
                model: openAIOptions.ModelId,
                credential: new ApiKeyCredential(openAIOptions.ApiKey));
        }
        else if (azureOpenAIOptions is not null && azureOpenAIOptions.IsValid)
        {
            var client = new AzureOpenAIClient(
                endpoint: new Uri(azureOpenAIOptions.Endpoint),
                credential: new ApiKeyCredential(azureOpenAIOptions.ApiKey));

            return client.GetRealtimeConversationClient(azureOpenAIOptions.DeploymentName);
        }
        else
        {
            throw new Exception("OpenAI/Azure OpenAI configuration was not found.");
        }
    }

    #endregion
}
