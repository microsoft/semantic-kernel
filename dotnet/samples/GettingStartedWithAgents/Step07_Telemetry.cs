// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Azure.Monitor.OpenTelemetry.Exporter;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
using OpenTelemetry;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

namespace GettingStarted;

/// <summary>
/// A repeat of <see cref="Step03_Chat"/> with telemetry enabled.
/// </summary>
public class Step07_Telemetry(ITestOutputHelper output) : BaseAssistantTest(output)
{
    /// <summary>
    /// Instance of <see cref="ActivitySource"/> for the example's main activity.
    /// </summary>
    private static readonly ActivitySource s_activitySource = new("AgentsTelemetry.Example");

    /// <summary>
    /// Demonstrates logging in <see cref="ChatCompletionAgent"/>, <see cref="OpenAIAssistantAgent"/> and <see cref="AgentGroupChat"/>.
    /// Logging is enabled through the <see cref="Agent.LoggerFactory"/> and <see cref="AgentChat.LoggerFactory"/> properties.
    /// This example uses <see cref="XunitLogger"/> to output logs to the test console, but any compatible logging provider can be used.
    /// </summary>
    [Fact]
    public async Task Logging()
    {
        await RunExampleAsync(loggerFactory: this.LoggerFactory);

        // Output:
        // [AddChatMessages] Adding Messages: 1.
        // [AddChatMessages] Added Messages: 1.
        // [InvokeAsync] Invoking chat: Microsoft.SemanticKernel.Agents.ChatCompletionAgent:63c505e8-cf5b-4aa3-a6a5-067a52377f82/CopyWriter, Microsoft.SemanticKernel.Agents.ChatCompletionAgent:85f6777b-54ef-4392-9608-67bc85c42c5b/ArtDirector
        // [InvokeAsync] Selecting agent: Microsoft.SemanticKernel.Agents.Chat.SequentialSelectionStrategy.
        // [NextAsync] Selected agent (0 / 2): 63c505e8-cf5b-4aa3-a6a5-067a52377f82/CopyWriter
        // and more...
    }

    /// <summary>
    /// Demonstrates tracing in <see cref="ChatCompletionAgent"/> and <see cref="OpenAIAssistantAgent"/>.
    /// Tracing is enabled through the <see cref="TracerProvider"/>.
    /// For output this example uses Console as well as Application Insights.
    /// </summary>
    [Theory]
    [InlineData(true, false)]
    [InlineData(false, false)]
    [InlineData(true, true)]
    [InlineData(false, true)]
    public async Task Tracing(bool useApplicationInsights, bool useStreaming)
    {
        using var tracerProvider = GetTracerProvider(useApplicationInsights);

        using var activity = s_activitySource.StartActivity("MainActivity");
        Console.WriteLine($"Operation/Trace ID: {Activity.Current?.TraceId}");

        await RunExampleAsync(useStreaming: useStreaming);

        // Output:
        // Operation/Trace ID: 132d831ef39c13226cdaa79873f375b8
        // Activity.TraceId:            132d831ef39c13226cdaa79873f375b8
        // Activity.SpanId:             891e8f2f32a61123
        // Activity.TraceFlags:         Recorded
        // Activity.ParentSpanId:       5dae937c9438def9
        // Activity.ActivitySourceName: Microsoft.SemanticKernel.Diagnostics
        // Activity.DisplayName:        chat.completions gpt-4
        // Activity.Kind:               Client
        // Activity.StartTime:          2025-02-03T23:32:57.1363560Z
        // Activity.Duration:           00:00:02.1339320
        // and more...
    }

    #region private

    private async Task RunExampleAsync(
        bool useStreaming = false,
        ILoggerFactory? loggerFactory = null)
    {
        // Define the agents
        ChatCompletionAgent agentReviewer =
            new()
            {
                Name = "ArtDirector",
                Instructions =
                    """
                    You are an art director who has opinions about copywriting born of a love for David Ogilvy.
                    The goal is to determine if the given copy is acceptable to print.
                    If so, state that it is approved.
                    If not, provide insight on how to refine suggested copy without examples.
                    """,
                Description = "An art director who has opinions about copywriting born of a love for David Ogilvy",
                Kernel = this.CreateKernelWithChatCompletion(),
                LoggerFactory = GetLoggerFactoryOrDefault(loggerFactory),
            };

        // Define the assistant
        Assistant assistant =
            await this.AssistantClient.CreateAssistantAsync(
                this.Model,
                name: "CopyWriter",
                instructions:
                    """
                    You are a copywriter with ten years of experience and are known for brevity and a dry humor.
                    The goal is to refine and decide on the single best copy as an expert in the field.
                    Only provide a single proposal per response.
                    You're laser focused on the goal at hand.
                    Don't waste time with chit chat.
                    Consider suggestions when refining an idea.
                    """,
                metadata: SampleMetadata);

        // Create the agent
        OpenAIAssistantAgent agentWriter = new(assistant, this.AssistantClient)
        {
            LoggerFactory = GetLoggerFactoryOrDefault(loggerFactory)
        };

        // Create a chat for agent interaction.
        AgentGroupChat chat =
            new(agentWriter, agentReviewer)
            {
                // This is all that is required to enable logging across the Agent Framework.
                LoggerFactory = GetLoggerFactoryOrDefault(loggerFactory),
                ExecutionSettings =
                    new()
                    {
                        // Here a TerminationStrategy subclass is used that will terminate when
                        // an assistant message contains the term "approve".
                        TerminationStrategy =
                            new ApprovalTerminationStrategy()
                            {
                                // Only the art-director may approve.
                                Agents = [agentReviewer],
                                // Limit total number of turns
                                MaximumIterations = 10,
                            }
                    }
            };

        // Invoke chat and display messages.
        ChatMessageContent input = new(AuthorRole.User, "concept: maps made out of egg cartons.");
        chat.AddChatMessage(input);
        this.WriteAgentChatMessage(input);

        if (useStreaming)
        {
            string lastAgent = string.Empty;
            await foreach (StreamingChatMessageContent response in chat.InvokeStreamingAsync())
            {
                if (string.IsNullOrEmpty(response.Content))
                {
                    continue;
                }

                if (!lastAgent.Equals(response.AuthorName, StringComparison.Ordinal))
                {
                    Console.WriteLine($"\n# {response.Role} - {response.AuthorName ?? "*"}:");
                    lastAgent = response.AuthorName ?? string.Empty;
                }

                Console.WriteLine($"\t > streamed: '{response.Content}'");
            }

            // Display the chat history.
            Console.WriteLine("================================");
            Console.WriteLine("CHAT HISTORY");
            Console.WriteLine("================================");

            ChatMessageContent[] history = await chat.GetChatMessagesAsync().Reverse().ToArrayAsync();

            for (int index = 0; index < history.Length; index++)
            {
                this.WriteAgentChatMessage(history[index]);
            }
        }
        else
        {
            await foreach (ChatMessageContent response in chat.InvokeAsync())
            {
                this.WriteAgentChatMessage(response);
            }
        }

        Console.WriteLine($"\n[IS COMPLETED: {chat.IsComplete}]");
    }

    private TracerProvider? GetTracerProvider(bool useApplicationInsights)
    {
        // Enable diagnostics.
        AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnostics", true);

        var tracerProviderBuilder = Sdk.CreateTracerProviderBuilder()
            .SetResourceBuilder(ResourceBuilder.CreateDefault().AddService("Semantic Kernel Agents Tracing Example"))
            .AddSource("Microsoft.SemanticKernel*")
            .AddSource(s_activitySource.Name);

        if (useApplicationInsights)
        {
            var connectionString = TestConfiguration.ApplicationInsights.ConnectionString;

            if (string.IsNullOrWhiteSpace(connectionString))
            {
                throw new ConfigurationNotFoundException(
                    nameof(TestConfiguration.ApplicationInsights),
                    nameof(TestConfiguration.ApplicationInsights.ConnectionString));
            }

            tracerProviderBuilder.AddAzureMonitorTraceExporter(o => o.ConnectionString = connectionString);
        }
        else
        {
            tracerProviderBuilder.AddConsoleExporter();
        }

        return tracerProviderBuilder.Build();
    }

    private ILoggerFactory GetLoggerFactoryOrDefault(ILoggerFactory? loggerFactory = null) => loggerFactory ?? NullLoggerFactory.Instance;

    private sealed class ApprovalTerminationStrategy : TerminationStrategy
    {
        // Terminate when the final message contains the term "approve"
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
            => Task.FromResult(history[history.Count - 1].Content?.Contains("approve", StringComparison.OrdinalIgnoreCase) ?? false);
    }

    #endregion
}
