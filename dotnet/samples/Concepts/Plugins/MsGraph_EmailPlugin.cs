// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Graph;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;

namespace Plugins;

/// <summary>
/// This example shows how to use Microsoft Graph Plugin
/// These examples require a valid Microsoft account and delegated/application access for the used resources.
/// </summary>
public class MsGraph_EmailPlugin(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>Shows how to use Microsoft Graph Email Plugin with AI Models.</summary>
    [Fact]
    public async Task EmailPlugin_SendEmailToMyself()
    {
        // Setup the Kernel
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatClient(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        using var graphClient = GetGraphClient();

        var emailConnector = new OutlookMailConnector(graphClient);

        // Add the plugin to the Kernel
        var graphPlugin = kernel.Plugins.AddFromObject(new Microsoft.SemanticKernel.Plugins.MsGraph.EmailPlugin(emailConnector));

        var settings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        const string Prompt = """
            Using the tools available, please do the following:
            1. Get my email address
            2. Send an email to myself with the subject "FYI" and content "This is a very important email"
            3. List 10 of my email messages
            """;

        // Invoke the Graph plugin with a prompt
        var result = await kernel.InvokePromptAsync(Prompt, new(settings));

        Console.WriteLine(result);
    }

    private static GraphServiceClient GetGraphClient()
    {
        var credential = new InteractiveBrowserCredential(new InteractiveBrowserCredentialOptions()
        {
            ClientId = TestConfiguration.MSGraph.ClientId,
            TenantId = TestConfiguration.MSGraph.TenantId,
            RedirectUri = TestConfiguration.MSGraph.RedirectUri,
        });

        return new GraphServiceClient(credential);
    }
}
