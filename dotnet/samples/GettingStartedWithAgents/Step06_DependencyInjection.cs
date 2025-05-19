// Copyright (c) Microsoft. All rights reserved.
using System.ClientModel;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted;

/// <summary>
/// Demonstrate creation of an agent via dependency injection.
/// </summary>
public class Step06_DependencyInjection(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string TutorName = "Tutor";
    private const string TutorInstructions =
        """
        Think step-by-step and rate the user input on creativity and expressiveness from 1-100.

        Respond in JSON format with the following JSON schema:

        {
            "score": "integer (1-100)",
            "notes": "the reason for your score"
        }
        """;

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseDependencyInjectionToCreateAgent(bool useChatClient)
    {
        ServiceCollection serviceContainer = new();

        serviceContainer.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));

        if (useChatClient)
        {
            IChatClient chatClient;
            if (this.UseOpenAIConfig)
            {
                chatClient = new OpenAI.OpenAIClient(TestConfiguration.OpenAI.ApiKey)
                    .GetChatClient(TestConfiguration.OpenAI.ChatModelId)
                    .AsIChatClient();
            }
            else if (!string.IsNullOrEmpty(this.ApiKey))
            {
                chatClient = new AzureOpenAIClient(
                        endpoint: new Uri(TestConfiguration.AzureOpenAI.Endpoint),
                        credential: new ApiKeyCredential(TestConfiguration.AzureOpenAI.ApiKey))
                    .GetChatClient(TestConfiguration.OpenAI.ChatModelId)
                    .AsIChatClient();
            }
            else
            {
                chatClient = new AzureOpenAIClient(
                        endpoint: new Uri(TestConfiguration.AzureOpenAI.Endpoint),
                        credential: new AzureCliCredential())
                    .GetChatClient(TestConfiguration.OpenAI.ChatModelId)
                    .AsIChatClient();
            }

            var functionCallingChatClient = chatClient!.AsBuilder().UseKernelFunctionInvocation().Build();
            serviceContainer.AddTransient<IChatClient>((sp) => functionCallingChatClient);
        }
        else
        {
            if (this.UseOpenAIConfig)
            {
                serviceContainer.AddOpenAIChatCompletion(
                    TestConfiguration.OpenAI.ChatModelId,
                    TestConfiguration.OpenAI.ApiKey);
            }
            else if (!string.IsNullOrEmpty(this.ApiKey))
            {
                serviceContainer.AddAzureOpenAIChatCompletion(
                    TestConfiguration.AzureOpenAI.ChatDeploymentName,
                    TestConfiguration.AzureOpenAI.Endpoint,
                    TestConfiguration.AzureOpenAI.ApiKey);
            }
            else
            {
                serviceContainer.AddAzureOpenAIChatCompletion(
                    TestConfiguration.AzureOpenAI.ChatDeploymentName,
                    TestConfiguration.AzureOpenAI.Endpoint,
                    new AzureCliCredential());
            }
        }

        // Transient Kernel as each agent may customize its Kernel instance with plug-ins.
        serviceContainer.AddTransient<Kernel>();

        serviceContainer.AddTransient<AgentClient>();

        serviceContainer.AddKeyedSingleton<ChatCompletionAgent>(
            TutorName,
            (sp, key) =>
                new ChatCompletionAgent()
                {
                    Instructions = TutorInstructions,
                    Name = TutorName,
                    Kernel = sp.GetRequiredService<Kernel>().Clone(),
                });

        // Create a service provider for resolving registered services
        await using ServiceProvider serviceProvider = serviceContainer.BuildServiceProvider();

        // If an application follows DI guidelines, the following line is unnecessary because DI will inject an instance of the AgentClient class to a class that references it.
        // DI container guidelines - https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines#recommendations
        AgentClient agentClient = serviceProvider.GetRequiredService<AgentClient>();

        // Execute the agent-client
        await WriteAgentResponse("The sunset is nice.");
        await WriteAgentResponse("The sunset is setting over the mountains.");
        await WriteAgentResponse("The sunset is setting over the mountains and filled the sky with a deep red flame, setting the clouds ablaze.");

        // Local function to invoke agent and display the conversation messages.
        async Task WriteAgentResponse(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agentClient.RunDemoAsync(message))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }

    private sealed class AgentClient([FromKeyedServices(TutorName)] ChatCompletionAgent agent)
    {
        private readonly AgentGroupChat _chat = new();

        public IAsyncEnumerable<ChatMessageContent> RunDemoAsync(ChatMessageContent input)
        {
            this._chat.AddChatMessage(input);

            return this._chat.InvokeAsync(agent);
        }
    }

    private record struct WritingScore(int score, string notes);
}
