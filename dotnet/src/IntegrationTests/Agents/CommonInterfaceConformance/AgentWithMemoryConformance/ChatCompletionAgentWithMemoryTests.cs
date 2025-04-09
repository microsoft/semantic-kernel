// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Memory;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithMemoryConformance;

public class ChatCompletionAgentWithMemoryTests() : AgentWithMemoryTests<ChatCompletionAgentFixture>(() => new ChatCompletionAgentFixture())
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<ChatCompletionAgentFixture>()
            .Build();

    [Fact]
    public virtual async Task MemoryComponentCapturesMemoriesFromUserInputAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;
        var memoryComponent = new UserPreferencesMemoryComponent(this.Fixture.Agent.Kernel);

        var agentThread1 = new ChatHistoryAgentThread();
        agentThread1.ThreadExtensionsManager.RegisterThreadExtension(memoryComponent);

        var agentThread2 = new ChatHistoryAgentThread();
        agentThread2.ThreadExtensionsManager.RegisterThreadExtension(memoryComponent);

        // Act
        var asyncResults1 = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Hello, my name is Caoimhe."), agentThread1);
        var results1 = await asyncResults1.ToListAsync();

        var asyncResults2 = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "What is my name?."), agentThread2);
        var results2 = await asyncResults2.ToListAsync();

        // Assert
        Assert.Contains("Caoimhe", results2.First().Message.Content);

        // Cleanup
        await this.Fixture.DeleteThread(agentThread1);
        await this.Fixture.DeleteThread(agentThread2);
    }

    [Fact]
    public virtual async Task MemoryComponentCapturesMemoriesInVectorStoreFromUserInputAsync()
    {
        // Arrange
        var config = this._configuration.GetRequiredSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();

        var vectorStore = new InMemoryVectorStore();
        var textEmbeddingService = new AzureOpenAITextEmbeddingGenerationService(config!.EmbeddingModelId, config.Endpoint, new AzureCliCredential());
        using var textMemoryStore = new VectorDataTextMemoryStore<string>(vectorStore, textEmbeddingService, "Memories", "user/12345", 1536);

        var agent = this.Fixture.Agent;

        // Act - First invocation with first thread.
        var agentThread1 = new ChatHistoryAgentThread();
        agentThread1.ThreadExtensionsManager.RegisterThreadExtension(new UserPreferencesMemoryComponent(this.Fixture.Agent.Kernel, textMemoryStore));

        var asyncResults1 = agent.InvokeAsync("Hello, my name is Caoimhe.", agentThread1);
        var results1 = await asyncResults1.ToListAsync();

        // Act - Second invocation with second thread.
        var agentThread2 = new ChatHistoryAgentThread();
        agentThread2.ThreadExtensionsManager.RegisterThreadExtension(new UserPreferencesMemoryComponent(this.Fixture.Agent.Kernel, textMemoryStore));

        var asyncResults2 = agent.InvokeAsync("What is my name?.", agentThread2);
        var results2 = await asyncResults2.ToListAsync();

        // Assert
        Assert.Contains("Caoimhe", results2.First().Message.Content);

        // Cleanup
        await this.Fixture.DeleteThread(agentThread1);
        await this.Fixture.DeleteThread(agentThread2);
    }
}
