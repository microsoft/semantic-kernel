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
/// These examples require a valid Microsoft account and delegated/application access for the Microsoft Graph used resources.
/// </summary>
public class MsGraph_CalendarPlugin(ITestOutputHelper output) : BaseTest(output)
{
    private static readonly JsonSerializerOptions s_options = new() { WriteIndented = true };

    /// <summary>Shows how to use Microsoft Graph Calendar Plugin with AI Models.</summary>
    [Fact]
    public async Task UsingWithAIModel()
    {
        // Setup the Kernel
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatClient(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        using var graphClient = GetGraphClient();

        var calendarConnector = new OutlookCalendarConnector(graphClient);

        // Add the plugin to the Kernel
        var graphPlugin = kernel.Plugins.AddFromObject(new CalendarPlugin(calendarConnector, jsonSerializerOptions: s_options));

        var settings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        string Prompt = $"""
            1. Show me the next 10 calendar events I have
            2. If I don't have any event named "Semantic Kernel", please create a new event named "Semantic Kernel"
            starting at {DateTimeOffset.Now.AddHours(1)} with 1 hour of duration.
            """;

        // Invoke the OneDrive plugin multiple times
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
