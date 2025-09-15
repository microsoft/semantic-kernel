// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class ChatCompletion_HistoryReducer(ITestOutputHelper output) : BaseTest(output)
{
    private const string TranslatorName = "NumeroTranslator";
    private const string TranslatorInstructions = "Add one to latest user number and spell it in spanish without explanation.";

    /// <summary>
    /// Demonstrate the use of <see cref="ChatHistoryTruncationReducer"/> when directly
    /// invoking a <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task TruncatedAgentReduction(bool useChatClient)
    {
        // Define the agent
        ChatCompletionAgent agent = CreateTruncatingAgent(10, 10, useChatClient, out var chatClient);

        await InvokeAgentAsync(agent, 50);

        chatClient?.Dispose();
    }

    /// <summary>
    /// Demonstrate the use of <see cref="ChatHistorySummarizationReducer"/> when directly
    /// invoking a <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task SummarizedAgentReduction(bool useChatClient)
    {
        // Define the agent
        ChatCompletionAgent agent = CreateSummarizingAgent(10, 10, useChatClient, out var chatClient);

        await InvokeAgentAsync(agent, 50);

        chatClient?.Dispose();
    }

    // Proceed with dialog by directly invoking the agent and explicitly managing the history.
    private async Task InvokeAgentAsync(ChatCompletionAgent agent, int messageCount)
    {
        ChatHistoryAgentThread agentThread = new();

        int index = 1;
        while (index <= messageCount)
        {
            // Provide user input
            Console.WriteLine($"# {AuthorRole.User}: '{index}'");

            // Reduce prior to invoking the agent
            bool isReduced = await agent.ReduceAsync(agentThread.ChatHistory);

            // Invoke and display assistant response
            await foreach (ChatMessageContent message in agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, $"{index}"), agentThread))
            {
                Console.WriteLine($"# {message.Role} - {message.AuthorName ?? "*"}: '{message.Content}'");
            }

            index += 2;

            // Display the message count of the chat-history for visibility into reduction
            Console.WriteLine($"@ Message Count: {agentThread.ChatHistory.Count}\n");

            // Display summary messages (if present) if reduction has occurred
            if (isReduced)
            {
                int summaryIndex = 0;
                while (agentThread.ChatHistory[summaryIndex].Metadata?.ContainsKey(ChatHistorySummarizationReducer.SummaryMetadataKey) ?? false)
                {
                    Console.WriteLine($"\tSummary: {agentThread.ChatHistory[summaryIndex].Content}");
                    ++summaryIndex;
                }
            }
        }
    }

    private ChatCompletionAgent CreateSummarizingAgent(int reducerMessageCount, int reducerThresholdCount, bool useChatClient, out IChatClient? chatClient)
    {
        Kernel kernel = this.CreateKernelWithChatCompletion(useChatClient, out chatClient);

        var service = useChatClient
            ? kernel.GetRequiredService<IChatClient>().AsChatCompletionService()
            : kernel.GetRequiredService<IChatCompletionService>();

        return
            new()
            {
                Name = TranslatorName,
                Instructions = TranslatorInstructions,
                Kernel = kernel,
                HistoryReducer = new ChatHistorySummarizationReducer(service, reducerMessageCount, reducerThresholdCount),
            };
    }

    private ChatCompletionAgent CreateTruncatingAgent(int reducerMessageCount, int reducerThresholdCount, bool useChatClient, out IChatClient? chatClient) =>
        new()
        {
            Name = TranslatorName,
            Instructions = TranslatorInstructions,
            Kernel = this.CreateKernelWithChatCompletion(useChatClient, out chatClient),
            HistoryReducer = new ChatHistoryTruncationReducer(reducerMessageCount, reducerThresholdCount),
        };
}
