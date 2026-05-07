// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
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
public class MsGraph_OrganizationHierarchyPlugin(ITestOutputHelper output) : BaseTest(output)
{
    private static readonly JsonSerializerOptions s_options = new() { WriteIndented = true };

    /// <summary>Shows how to use Microsoft Graph Organization Hierarchy Plugin with AI Models.</summary>
    [Fact]
    public async Task UsingWithAIModel()
    {
        // Setup the Kernel
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatClient(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        using var graphClient = GetGraphClient();
        var connector = new OrganizationHierarchyConnector(graphClient);

        // Add the plugin to the Kernel
        var graphPlugin = kernel.Plugins.AddFromObject(new OrganizationHierarchyPlugin(connector, s_options));

        var settings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        const string Prompt = "I need you to show my manager details as well as my direct reports using the tools available:";

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
