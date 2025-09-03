// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Graph;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.MsGraph;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;

namespace Plugins;

/// <summary>
/// This example shows how to use Microsoft Graph Plugin
/// These examples require a valid Microsoft account and delegated/application access for the used resources.
/// </summary>
public class MsGraph_OneDrivePlugin(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>Shows how to use Microsoft Graph OneDrive Plugin with AI Models.</summary>
    [Fact]
    public async Task UsingWithAIModel()
    {
        // Setup the Kernel
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatClient(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        using var graphClient = GetGraphClient();
        var connector = new OneDriveConnector(graphClient);

        // Add the plugin to the Kernel
        var graphPlugin = kernel.Plugins.AddFromObject(new CloudDrivePlugin(connector));

        var settings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        const string Prompt = """
            I need you to do the following things with the tools available:
            1. Update the current file: "Resources/travelinfo.txt" to my OneDrive into the "Test" folder.
            2. Generate a OneDrive Link for sharing the file
            3. Summarize for me the contents of the uploaded file
            4. Show me the generated shared link.
            """;

        // Invoke the OneDrive plugin multiple times
        var result = await kernel.InvokePromptAsync(Prompt, new(settings));

        Console.WriteLine($"Assistant: {result}");
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
