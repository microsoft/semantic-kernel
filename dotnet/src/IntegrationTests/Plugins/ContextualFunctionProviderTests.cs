// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Functions;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Plugins;

public sealed class ContextualFunctionProviderTests : BaseIntegrationTest, IDisposable
{
    private readonly VectorStore _vectorStore;
    private readonly Kernel _kernel;
    private readonly int _modelDimensions = 1536;

    public ContextualFunctionProviderTests(ITestOutputHelper output)
    {
        IConfigurationRoot configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<ContextualFunctionProviderTests>()
            .Build();

        var embeddingsConfig = configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>()!;
        var chatConfig = configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        var embeddingGenerator = new AzureOpenAIClient(new Uri(embeddingsConfig.Endpoint), new AzureCliCredential())
            .GetEmbeddingClient(embeddingsConfig.DeploymentName)
            .AsIEmbeddingGenerator();

        this._vectorStore = new InMemoryVectorStore(new InMemoryVectorStoreOptions() { EmbeddingGenerator = embeddingGenerator });

        var builder = Kernel.CreateBuilder();
        builder.AddAzureOpenAIChatCompletion(chatConfig.ChatDeploymentName!, chatConfig.Endpoint, new AzureCliCredential());
        this._kernel = builder.Build();
    }

    [Fact]
    private async Task ItShouldSelectFunctionsRelevantToCurrentInvocationContextAsync()
    {
        // Arrange
        IList<AIFunction>? relevantFunctions = null;

        void OnModelInvokingAsync(ICollection<ChatMessage> newMessages, AIContext context)
        {
            relevantFunctions = context.AIFunctions;
        }

        ChatCompletionAgent agent =
            new()
            {
                Name = "ReviewGuru",
                Instructions = "You are a friendly assistant that summarizes key points and sentiments from customer reviews.",
                Kernel = this._kernel,
                Arguments = new(new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new FunctionChoiceBehaviorOptions { RetainArgumentTypes = true }) })
            };

        ContextualFunctionProvider provider = new(
            vectorStore: this._vectorStore,
            vectorDimensions: this._modelDimensions,
            functions: GetAvailableFunctions(),
            maxNumberOfFunctions: 3
        );

        ChatHistoryAgentThread agentThread = new();
        agentThread.AIContextProviders.Add(new AIContextProviderDecorator(provider, OnModelInvokingAsync));

        // Act
        await agent.InvokeAsync("Get latest customer reviews and identify trends in sentiment.", agentThread).FirstAsync();

        // Assert
        Assert.NotNull(relevantFunctions);
        Assert.Contains(relevantFunctions, f => f.Name == "GetCustomerReviews");
        Assert.Contains(relevantFunctions, f => f.Name == "IdentifySentimentTrend");
    }

    [Fact]
    private async Task ItShouldSelectFunctionsBasedOnPreviousAndCurrentInvocationContextAsync()
    {
        // Arrange
        IList<AIFunction>? relevantFunctions = null;

        void OnModelInvokingAsync(ICollection<ChatMessage> newMessages, AIContext context)
        {
            relevantFunctions = context.AIFunctions;
        }

        ChatCompletionAgent agent =
            new()
            {
                Name = "AzureAssistant",
                Instructions = "You are a helpful assistant that helps with Azure resource management. " +
                               "Avoid including the phrase like 'If you need further assistance or have any additional tasks, feel free to let me know!' in any responses.",
                Kernel = this._kernel,
                Arguments = new(new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new FunctionChoiceBehaviorOptions { RetainArgumentTypes = true }) })
            };

        ContextualFunctionProvider provider = new(
            vectorStore: this._vectorStore,
            vectorDimensions: this._modelDimensions,
            functions: GetAvailableFunctions(),
            maxNumberOfFunctions: 1, // Instruct the provider to return only one relevant function
            options: new ContextualFunctionProviderOptions
            {
                NumberOfRecentMessagesInContext = 1, // Use only the last message from the previous agent invocation
                ContextEmbeddingValueProvider = (recentMessages, newMessages, _) =>
                {
                    string context;

                    // Provide a deterministic context for the VM deployment request instead of using the one assembled by the provider based on
                    // the LLM's non-deterministic response for the VM provisioning request. This is done to ensure that the context is always
                    // the same for the VM deployment request; otherwise, the non-deterministic context could lead to different function selection
                    // results for the same VM deployment request, resulting in test flakiness.  
                    if (newMessages.Any(m => m.Text.Contains("Deploy it")))
                    {
                        context = "A VM has been successfully provisioned with the ID: 40a2d11e-233b-409e-8638-9d4508623b93.\r\nDeploy it";
                    }
                    else
                    {
                        context = string.Join(
                            Environment.NewLine,
                            recentMessages
                            .TakeLast(1)
                            .Where(m => !string.IsNullOrWhiteSpace(m?.Text))
                            .Select(m => m.Text));
                    }

                    return Task.FromResult(context);
                },
            }
        );

        ChatHistoryAgentThread agentThread = new();
        agentThread.AIContextProviders.Add(new AIContextProviderDecorator(provider, OnModelInvokingAsync));

        // Act
        await agent.InvokeAsync("Please provision a VM on Azure", agentThread).FirstAsync();

        // Assert
        Assert.NotNull(relevantFunctions);
        Assert.Single(relevantFunctions, f => f.Name == "ProvisionVM");

        // Act: Ask agent to deploy the VM provisioned in the previous invocation
        await agent.InvokeAsync("Deploy it", agentThread).FirstAsync();

        // Assert
        Assert.NotNull(relevantFunctions);
        Assert.Single(relevantFunctions, f => f.Name == "DeployVM");
    }

    /// <summary>
    /// Returns a list of functions that belong to different categories.
    /// Some categories/functions are related to the prompt, while others
    /// are not. This is intentionally done to demonstrate the contextual
    /// function selection capabilities of the provider.
    /// </summary>
    private static IReadOnlyList<AIFunction> GetAvailableFunctions()
    {
        List<AIFunction> reviewFunctions = [
            AIFunctionFactory.Create(() => """
            [  
                {  
                    "reviewer": "John D.",  
                    "date": "2023-10-01",  
                    "rating": 5,  
                    "comment": "Great product and fast shipping!"  
                },  
                {  
                    "reviewer": "Jane S.",  
                    "date": "2023-09-28",  
                    "rating": 4,  
                    "comment": "Good quality, but delivery was a bit slow."  
                },  
                {  
                    "reviewer": "Mike J.",  
                    "date": "2023-09-25",  
                    "rating": 3,  
                    "comment": "Average. Works as expected."  
                }  
            ]
            """
            , "GetCustomerReviews"),
        ];

        List<AIFunction> sentimentFunctions = [
            AIFunctionFactory.Create((string text) => "The collected sentiment is mostly positive with a few neutral and negative opinions.", "CollectSentiments"),
            AIFunctionFactory.Create((string text) => "Sentiment trend identified: predominantly positive with increasing positive feedback.", "IdentifySentimentTrend"),
        ];

        List<AIFunction> summaryFunctions = [
            AIFunctionFactory.Create((string text) => "Summary generated based on input data: key points include market growth and customer satisfaction.", "Summarize"),
            AIFunctionFactory.Create((string text) => "Extracted themes: innovation, efficiency, customer satisfaction.", "ExtractThemes"),
        ];

        List<AIFunction> communicationFunctions = [
            AIFunctionFactory.Create((string address, string content) => "Email sent.", "SendEmail"),
            AIFunctionFactory.Create((string number, string text) => "Message sent.", "SendSms"),
            AIFunctionFactory.Create(() => "user@domain.com", "MyEmail"),
        ];

        List<AIFunction> dateTimeFunctions = [
            AIFunctionFactory.Create(() => DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"), "GetCurrentDateTime"),
            AIFunctionFactory.Create(() => DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss"), "GetCurrentUtcDateTime"),
        ];

        List<AIFunction> azureFunctions = [
            AIFunctionFactory.Create(() => $"Resource group provisioned: Id:{Guid.NewGuid()}", "ProvisionResourceGroup"),
            AIFunctionFactory.Create((Guid id) => $"Resource group deployed: Id:{id}", "DeployResourceGroup"),

            AIFunctionFactory.Create(() => $"Storage account provisioned: Id:{Guid.NewGuid()}", "ProvisionStorageAccount"),
            AIFunctionFactory.Create((Guid id) => $"Storage account deployed: Id:{id}", "DeployStorageAccount"),

            AIFunctionFactory.Create(() => $"VM provisioned: Id:{Guid.NewGuid()}", "ProvisionVM"),
            AIFunctionFactory.Create((Guid id) => $"VM deployed: Id:{id}", "DeployVM"),
        ];

        return [.. reviewFunctions, .. sentimentFunctions, .. summaryFunctions, .. communicationFunctions, .. dateTimeFunctions, .. azureFunctions];
    }

    public void Dispose()
    {
        this._vectorStore.Dispose();
    }

    private sealed class AIContextProviderDecorator : AIContextProvider
    {
        private readonly Action<ICollection<ChatMessage>, AIContext>? _onModelInvokingAsync;
        private readonly AIContextProvider _inner;

        public AIContextProviderDecorator(AIContextProvider inner, Action<ICollection<ChatMessage>, AIContext>? onModelInvokingAsync)
        {
            this._inner = inner;
            this._onModelInvokingAsync = onModelInvokingAsync;
        }

        public override async Task<AIContext> ModelInvokingAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
        {
            var result = await this._inner.ModelInvokingAsync(newMessages, cancellationToken).ConfigureAwait(false);

            this._onModelInvokingAsync?.Invoke(newMessages, result);

            return result;
        }

        public override Task ConversationCreatedAsync(string? conversationId, CancellationToken cancellationToken = default)
        {
            return this._inner.ConversationCreatedAsync(conversationId, cancellationToken);
        }

        public override Task MessageAddingAsync(string? conversationId, ChatMessage newMessage, CancellationToken cancellationToken = default)
        {
            return this._inner.MessageAddingAsync(conversationId, newMessage, cancellationToken);
        }

        public override Task ConversationDeletingAsync(string? conversationId, CancellationToken cancellationToken = default)
        {
            return this._inner.ConversationDeletingAsync(conversationId, cancellationToken);
        }
    }
}
