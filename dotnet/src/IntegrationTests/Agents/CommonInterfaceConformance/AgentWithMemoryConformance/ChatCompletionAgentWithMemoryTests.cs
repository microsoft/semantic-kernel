// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Memory;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.TextRag;
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

    [Fact(Skip = "For manual verification")]
    public virtual async Task Mem0ComponentCapturesMemoriesFromUserInputAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;

        using var httpClient = new HttpClient();
        httpClient.BaseAddress = new Uri("https://api.mem0.ai");
        httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Token", "<APIKey>");

        var mem0Component = new Mem0MemoryComponent(httpClient, new() { UserId = "U1" });

        var agentThread1 = new ChatHistoryAgentThread();
        agentThread1.ThreadExtensionsManager.RegisterThreadExtension(mem0Component);

        var agentThread2 = new ChatHistoryAgentThread();
        agentThread2.ThreadExtensionsManager.RegisterThreadExtension(mem0Component);

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
    public virtual async Task MemoryComponentCapturesMemoriesFromUserInputAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;
        var memoryComponent = new UserFactsMemoryComponent(this.Fixture.Agent.Kernel);

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
        agentThread1.ThreadExtensionsManager.RegisterThreadExtension(new UserFactsMemoryComponent(this.Fixture.Agent.Kernel, textMemoryStore));

        var asyncResults1 = agent.InvokeAsync("Hello, my name is Caoimhe.", agentThread1);
        var results1 = await asyncResults1.ToListAsync();

        // Act - Second invocation with second thread.
        var agentThread2 = new ChatHistoryAgentThread();
        agentThread2.ThreadExtensionsManager.RegisterThreadExtension(new UserFactsMemoryComponent(this.Fixture.Agent.Kernel, textMemoryStore));

        var asyncResults2 = agent.InvokeAsync("What is my name?.", agentThread2);
        var results2 = await asyncResults2.ToListAsync();

        // Assert
        Assert.Contains("Caoimhe", results2.First().Message.Content);

        // Cleanup
        await this.Fixture.DeleteThread(agentThread1);
        await this.Fixture.DeleteThread(agentThread2);
    }

    [Fact]
    public virtual async Task CapturesMemoriesWhileUsingDIAsync()
    {
        var chatConfig = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;
        var embeddingConfig = this._configuration.GetRequiredSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();

        // Arrange - Setup DI container.
        var builder = Host.CreateEmptyApplicationBuilder(settings: null);
        builder.Services.AddKernel();
        builder.Services.AddInMemoryVectorStore();
        builder.Services.AddAzureOpenAIChatCompletion(
            deploymentName: chatConfig.ChatDeploymentName!,
            endpoint: chatConfig.Endpoint,
            credentials: new AzureCliCredential());
        builder.Services.AddAzureOpenAITextEmbeddingGeneration(
            embeddingConfig!.EmbeddingModelId,
            embeddingConfig.Endpoint,
            new AzureCliCredential());
        builder.Services.AddKeyedTransient<TextMemoryStore, VectorDataTextMemoryStore<string>>("UserFactsStore", (sp, _) => new VectorDataTextMemoryStore<string>(
            sp.GetRequiredService<IVectorStore>(),
            sp.GetRequiredService<ITextEmbeddingGenerationService>(),
            "Memories", "user/12345", 1536));
        builder.Services.AddTransient<ConversationStateExtension, UserFactsMemoryComponent>();
        builder.Services.AddTransient<AgentThread>((sp) =>
        {
            var thread = new ChatHistoryAgentThread();
            thread.ThreadExtensionsManager.RegisterThreadExtensionsFromContainer(sp);
            return thread;
        });
        var host = builder.Build();

        // Arrange - Create agent.
        var agent = new ChatCompletionAgent()
        {
            Kernel = host.Services.GetRequiredService<Kernel>(),
            Instructions = "You are a helpful assistant.",
        };

        // Act - First invocation
        var agentThread1 = host.Services.GetRequiredService<AgentThread>();

        var asyncResults1 = agent.InvokeAsync("Hello, my name is Caoimhe.", agentThread1);
        var results1 = await asyncResults1.ToListAsync();

        // Act - Call suspend on the thread, so that all memory components attached to it, save their state.
        await agentThread1.OnSuspendAsync(default);

        // Act - Second invocation
        var agentThread2 = host.Services.GetRequiredService<AgentThread>();

        var asyncResults2 = agent.InvokeAsync("What is my name?.", agentThread2);
        var results2 = await asyncResults2.ToListAsync();

        // Assert
        Assert.Contains("Caoimhe", results2.First().Message.Content);

        // Cleanup
        await this.Fixture.DeleteThread(agentThread1);
        await this.Fixture.DeleteThread(agentThread2);
    }

    [Fact]
    public virtual async Task RagComponentWithoutMatchesAsync()
    {
        // Arrange - Create Embedding Service
        var config = this._configuration.GetRequiredSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        var textEmbeddingService = new AzureOpenAITextEmbeddingGenerationService(config!.EmbeddingModelId, config.Endpoint, new AzureCliCredential());

        // Arrange - Create Vector Store and Rag Store/Component
        var vectorStore = new InMemoryVectorStore();
        using var ragStore = new TextRagStore<string>(vectorStore, textEmbeddingService, "FinancialData", 1536, "group/g1");
        var ragComponent = new TextRagComponent(ragStore, new TextRagComponentOptions());

        // Arrange - Upsert documents into the Rag Store
        await ragStore.UpsertDocumentsAsync(GetSampleDocuments());

        var agent = this.Fixture.Agent;

        // Act - Create a new agent thread and register the Rag component
        var agentThread = new ChatHistoryAgentThread();
        agentThread.ThreadExtensionsManager.RegisterThreadExtension(ragComponent);

        // Act - Invoke the agent with a question
        var asyncResults1 = agent.InvokeAsync("What was the income of Contoso for 2023", agentThread);
        var results1 = await asyncResults1.ToListAsync();

        // Assert - Check if the response does not contain the expected value from the database because
        // we filtered by group/g1 which doesn't include the required document.
        Assert.DoesNotContain("174", results1.First().Message.Content);

        // Cleanup
        await this.Fixture.DeleteThread(agentThread);
    }

    [Fact]
    public virtual async Task RagComponentWithMatchesAsync()
    {
        // Arrange - Create Embedding Service
        var config = this._configuration.GetRequiredSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        var textEmbeddingService = new AzureOpenAITextEmbeddingGenerationService(config!.EmbeddingModelId, config.Endpoint, new AzureCliCredential());

        // Arrange - Create Vector Store and Rag Store/Component
        var vectorStore = new InMemoryVectorStore();
        using var ragStore = new TextRagStore<string>(vectorStore, textEmbeddingService, "FinancialData", 1536, "group/g2");
        var ragComponent = new TextRagComponent(ragStore, new TextRagComponentOptions());

        // Arrange - Upsert documents into the Rag Store
        await ragStore.UpsertDocumentsAsync(GetSampleDocuments());

        var agent = this.Fixture.Agent;

        // Act - Create a new agent thread and register the Rag component
        var agentThread = new ChatHistoryAgentThread();
        agentThread.ThreadExtensionsManager.RegisterThreadExtension(ragComponent);

        // Act - Invoke the agent with a question
        var asyncResults1 = agent.InvokeAsync("What was the income of Contoso for 2023", agentThread);
        var results1 = await asyncResults1.ToListAsync();

        // Assert - Check if the response contains the expected value from the database.
        Assert.Contains("174", results1.First().Message.Content);

        // Cleanup
        await this.Fixture.DeleteThread(agentThread);
    }

    [Fact]
    public virtual async Task RagComponentWithMatchesOnDemandAsync()
    {
        // Arrange - Create Embedding Service
        var config = this._configuration.GetRequiredSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        var textEmbeddingService = new AzureOpenAITextEmbeddingGenerationService(config!.EmbeddingModelId, config.Endpoint, new AzureCliCredential());

        // Arrange - Create Vector Store and Rag Store/Component
        var vectorStore = new InMemoryVectorStore();
        using var ragStore = new TextRagStore<string>(vectorStore, textEmbeddingService, "FinancialData", 1536, "group/g2");
        var ragComponent = new TextRagComponent(
            ragStore,
            new()
            {
                SearchTime = TextRagComponentOptions.TextRagSearchTime.ViaPlugin,
                PluginSearchFunctionName = "SearchCorporateData",
                PluginSearchFunctionDescription = "RAG Search over dataset containing financial data and company information about various companies."
            });

        // Arrange - Upsert documents into the Rag Store
        await ragStore.UpsertDocumentsAsync(GetSampleDocuments());

        var agent = this.Fixture.Agent;

        // Act - Create a new agent thread and register the Rag component
        var agentThread = new ChatHistoryAgentThread();
        agentThread.ThreadExtensionsManager.RegisterThreadExtension(ragComponent);

        // Act - Invoke the agent with a question
        var asyncResults1 = agent.InvokeAsync("What was the income of Contoso for 2023", agentThread, new() { KernelArguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }) });
        var results1 = await asyncResults1.ToListAsync();

        // Assert - Check if the response contains the expected value from the database.
        Assert.Contains("174", results1.First().Message.Content);

        // Cleanup
        await this.Fixture.DeleteThread(agentThread);
    }

    private static IEnumerable<TextRagDocument> GetSampleDocuments()
    {
        yield return new TextRagDocument("The financial results of Contoso Corp for 2024 is as follows:\nIncome EUR 154 000 000\nExpenses EUR 142 000 000")
        {
            SourceName = "Contoso 2024 Financial Report",
            SourceReference = "https://www.consoso.com/reports/2024.pdf",
            Namespaces = ["group/g1"]
        };
        yield return new TextRagDocument("The financial results of Contoso Corp for 2023 is as follows:\nIncome EUR 174 000 000\nExpenses EUR 152 000 000")
        {
            SourceName = "Contoso 2023 Financial Report",
            SourceReference = "https://www.consoso.com/reports/2023.pdf",
            Namespaces = ["group/g2"]
        };
        yield return new TextRagDocument("The financial results of Contoso Corp for 2022 is as follows:\nIncome EUR 184 000 000\nExpenses EUR 162 000 000")
        {
            SourceName = "Contoso 2022 Financial Report",
            SourceReference = "https://www.consoso.com/reports/2022.pdf",
            Namespaces = ["group/g2"]
        };
        yield return new TextRagDocument("The Contoso Corporation is a multinational business with its headquarters in Paris. The company is a manufacturing, sales, and support organization with more than 100,000 products.")
        {
            SourceName = "About Contoso",
            SourceReference = "https://www.consoso.com/about-us",
            Namespaces = ["group/g2"]
        };
        yield return new TextRagDocument("The financial results of AdventureWorks for 2021 is as follows:\nIncome USD 223 000 000\nExpenses USD 210 000 000")
        {
            SourceName = "AdventureWorks 2021 Financial Report",
            SourceReference = "https://www.adventure-works.com/reports/2021.pdf",
            Namespaces = ["group/g1", "group/g2"]
        };
        yield return new TextRagDocument("AdventureWorks is a large American business that specializaes in adventure parks and family entertainment.")
        {
            SourceName = "About AdventureWorks",
            SourceReference = "https://www.adventure-works.com/about-us",
            Namespaces = ["group/g1", "group/g2"]
        };
    }
}
