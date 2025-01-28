// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.AI.CrewAI;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="CrewAI_Plugin"/>.
/// </summary>
public class CrewAI_Plugin(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="CrewAI_Plugin"/> and use it to invoke a Crew.
    /// </summary>
    [Fact]
    public async Task UsingCrewAIEnterpriseAsync()
    {
        string crewAIEndpoint = TestConfiguration.CrewAI.Endpoint;
        string crewAIAuthToken = TestConfiguration.CrewAI.AuthToken;

        var crew = new CrewAIEnterprise(
            endpoint: new Uri(crewAIEndpoint),
            authTokenProvider: async () => crewAIAuthToken);

        var inputs = new
        {
            company = "Microsoft",
            topic = "Consumer AI Products",
        };

        // Invoke directly with inputs
        var result = await crew.KickoffAsync(inputs);
        Console.WriteLine(result);

        // Create a plugin with input descriptions and types
        var crewPlugin = crew.CreateKernelPlugin(
            name: "myCrew",
            description: "Conducts thorough research on topic to identify emerging trends, analyze competitor strategies, and gather data-driven insights, focusing on 2024.",
            inputDefinitions: [
                new ("company", "The name of the company that should be researched", typeof(string)),
                new ("topic", "The topic that should be researched", typeof(string)),
            ]);
    }

    [Fact]
    public async Task UsingCrewAIEnterpriseAsPluginAsync()
    {
        string crewAIEndpoint = TestConfiguration.CrewAI.Endpoint;
        string crewAIAuthToken = TestConfiguration.CrewAI.AuthToken;
        string openAIModelId = TestConfiguration.OpenAI.ChatModelId;
        string openAIApiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAIModelId is null || openAIApiKey is null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");
            return;
        }

        // Setup the Kernel and AI Services
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIModelId,
                apiKey: openAIApiKey)
            .Build();

        var crew = new CrewAIEnterprise(
            endpoint: new Uri(crewAIEndpoint),
            authTokenProvider: async () => crewAIAuthToken);

        var inputs = new
        {
            company = "Microsoft",
            topic = "Consumer AI Products",
        };

        var crewPlugin = crew.CreateKernelPlugin(
            "myCrew",
            "Conducts thorough research on topic to identify emerging trends, analyze competitor strategies, and gather data-driven insights, focusing on 2024.",
            [
                new ("company", "The name of the company that should be researched", typeof(string)),
                new ("topic", "The topic that should be researched", typeof(string)),
            ]);

        kernel.Plugins.Add(crewPlugin);
        var result = await kernel.InvokeAsync(crewPlugin["kickoff"], new() { ["company"] = inputs.company, ["topic"] = inputs.topic });
        Console.WriteLine(result);
    }
}
