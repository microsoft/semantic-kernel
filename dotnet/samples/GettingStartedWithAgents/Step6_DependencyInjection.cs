// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace GettingStarted;

/// <summary>
/// Demonstrate creation of an agent via dependency injection.
/// </summary>
public class Step6_DependencyInjection(ITestOutputHelper output) : BaseTest(output)
{
    private const int ScoreCompletionThreshold = 70;

    private const string TutorName = "Tutor";
    private const string TutorInstructions =
        """
        Think step-by-step and rate the user input on creativity and expressivness from 1-100.

        Respond in JSON format with the following JSON schema:

        {
            "score": "integer (1-100)",
            "notes": "the reason for your score"
        }
        """;

    [Fact]
    public async Task RunAsync()
    {
        ServiceCollection serviceContainer = new();

        serviceContainer.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));

        if (this.UseOpenAIConfig)
        {
            serviceContainer.AddOpenAIChatCompletion(
                TestConfiguration.OpenAI.ChatModelId,
                TestConfiguration.OpenAI.ApiKey);
        }
        else
        {
            serviceContainer.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);
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
                    Kernel = sp.GetRequiredService<Kernel>(),
                });

        // Create a service provider for resolving registered services
        await using ServiceProvider serviceProvider = serviceContainer.BuildServiceProvider();

        // If an application follows DI guidelines, the following line is unnecessary because DI will inject an instance of the AgentClient class to a class that references it.
        // DI container guidelines - https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection-guidelines#recommendations
        AgentClient agentClient = serviceProvider.GetRequiredService<AgentClient>();

        // Execute the agent-client
        await WriteAgentResponse("The sunset is very colorful.");
        await WriteAgentResponse("The sunset is setting over the mountains.");
        await WriteAgentResponse("The sunset is setting over the mountains and filled the sky with a deep red flame, setting the clouds ablaze.");

        // Local function to invoke agent and display the conversation messages.
        async Task WriteAgentResponse(string input)
        {
            Console.WriteLine($"# {AuthorRole.User}: {input}");

            await foreach (var content in agentClient.RunDemoAsync(input))
            {
                Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }
    }

    private sealed class AgentClient([FromKeyedServices(TutorName)] ChatCompletionAgent agent)
    {
        private readonly AgentGroupChat _chat =
            new()
            {
                ExecutionSettings =
                    new()
                    {
                        // Here a TerminationStrategy subclass is used that will terminate when
                        // the response includes a score that is greater than or equal to 70.
                        TerminationStrategy = new ThresholdTerminationStrategy()
                    }
            };

        public IAsyncEnumerable<ChatMessageContent> RunDemoAsync(string input)
        {
            // Create a chat for agent interaction.

            this._chat.Add(new ChatMessageContent(AuthorRole.User, input));

            return this._chat.InvokeAsync(agent);
        }
    }

    private record struct InputScore(int score, string notes);

    private sealed class ThresholdTerminationStrategy : TerminationStrategy
    {
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
        {
            string lastMessageContent = history[history.Count - 1].Content ?? string.Empty;

            InputScore? result = JsonResultTranslator.Translate<InputScore>(lastMessageContent);

            return Task.FromResult((result?.score ?? 0) >= ScoreCompletionThreshold);
        }
    }
}
