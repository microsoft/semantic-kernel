// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;
/// <summary>
/// Demonstrate that two different agent types are able to participate in the same conversation.
/// In this case a <see cref="ChatCompletionAgent"/> and <see cref="OpenAIAssistantAgent"/> participate.
/// </summary>
public class MixedChat_Serialization(ITestOutputHelper output) : BaseTest(output)
{
    private const string TranslatorName = "Translator";
    private const string TranslatorInstructions =
        """
        Spell the very last number in chat as a word in english and spanish
        """;

    private const string CounterName = "Counter";
    private const string CounterInstructions =
        """
        Add 1 to the very last number in the chat.
        
        Only respond with a single number that is the result of your calculation without explanation.
        """;

    [Fact]
    public async Task SerializeAndRestoreAgentGroupChatAsync()
    {
        // Define the agents: one of each type
        ChatCompletionAgent agentTranslator =
            new()
            {
                Instructions = TranslatorInstructions,
                Name = TranslatorName,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        OpenAIAssistantAgent agentCounter =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: new(),
                config: new(this.ApiKey, this.Endpoint),
                definition: new()
                {
                    Instructions = CounterInstructions,
                    Name = CounterName,
                    ModelId = this.Model,
                });

        AgentGroupChat chat = CreateGroupChat();

        // Invoke chat and display messages.
        string input = "1";
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));
        Console.WriteLine($"# {AuthorRole.User}: '{input}'");

        Console.WriteLine("============= Source Chat ==============");
        await InvokeAgents(chat);

        AgentGroupChat copy = CreateGroupChat();
        Console.WriteLine("\n=========== Serialized Chat ============");
        await CloneChatAsync(chat, copy);

        Console.WriteLine("\n============ Cloned Chat ===============");
        await InvokeAgents(copy);

        Console.WriteLine("\n============ Full History ==============");
        await foreach (ChatMessageContent content in copy.GetChatMessagesAsync())
        {
            Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
        }

        async Task InvokeAgents(AgentGroupChat chat)
        {
            await foreach (ChatMessageContent content in chat.InvokeAsync())
            {
                Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }

        async Task CloneChatAsync(AgentGroupChat source, AgentGroupChat clone)
        {
            await using MemoryStream stream = new();
            await AgentChatSerializer.SerializeAsync(source, stream);

            stream.Position = 0;
            using StreamReader reader = new(stream);
            Console.WriteLine(await reader.ReadToEndAsync());

            stream.Position = 0;
            AgentChatSerializer serializer = await AgentChatSerializer.DeserializeAsync(stream);
            await serializer.DeserializeAsync(clone);
        }

        AgentGroupChat CreateGroupChat() =>
            new(agentTranslator, agentCounter)
            {
                ExecutionSettings =
                    new()
                    {
                        TerminationStrategy =
                            new CountingTerminationStrategy(5)
                            {
                                // Only the art-director may approve.
                                Agents = [agentTranslator],
                                // Limit total number of turns
                                MaximumIterations = 20,
                            }
                    }
            };
    }

    private sealed class CountingTerminationStrategy(int maxTurns) : TerminationStrategy
    {
        private int _count = 0;

        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
        {
            ++this._count;

            bool shouldTerminate = this._count >= maxTurns;

            return Task.FromResult(shouldTerminate);
        }
    }
}
