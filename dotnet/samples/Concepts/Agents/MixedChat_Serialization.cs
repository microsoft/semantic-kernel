// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;

namespace Agents;
/// <summary>
/// Demonstrate the serialization of <see cref="AgentGroupChat"/> with a <see cref="ChatCompletionAgent"/>
/// and an <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public class MixedChat_Serialization(ITestOutputHelper output) : BaseAssistantTest(output)
{
    private const string TranslatorName = "Translator";
    private const string TranslatorInstructions =
        """
        Spell the last number in chat as a word in english and spanish on a single line without any line breaks.
        """;

    private const string CounterName = "Counter";
    private const string CounterInstructions =
        """
        Increment the last number from your most recent response.
        Never repeat the same number.
        
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

        // Define the assistant
        Assistant assistant =
            await this.AssistantClient.CreateAssistantAsync(
                this.Model,
                name: CounterName,
                instructions: CounterInstructions,
                metadata: SampleMetadata);

        // Create the agent
        OpenAIAssistantAgent agentCounter = new(assistant, this.AssistantClient);

        AgentGroupChat chat = CreateGroupChat();

        // Invoke chat and display messages.
        ChatMessageContent input = new(AuthorRole.User, "1");
        chat.AddChatMessage(input);
        this.WriteAgentChatMessage(input);

        Console.WriteLine("============= Dynamic Agent Chat - Primary (prior to serialization) ==============");
        await InvokeAgents(chat);

        AgentGroupChat copy = CreateGroupChat();
        Console.WriteLine("\n=========== Serialize and restore the Agent Chat into a new instance ============");
        await CloneChatAsync(chat, copy);

        Console.WriteLine("\n============ Continue with the dynamic Agent Chat (after deserialization) ===============");
        await InvokeAgents(copy);

        Console.WriteLine("\n============ The entire Agent Chat (includes messages prior to serialization and those after deserialization) ==============");
        await foreach (ChatMessageContent content in copy.GetChatMessagesAsync())
        {
            this.WriteAgentChatMessage(content);
        }

        async Task InvokeAgents(AgentGroupChat chat)
        {
            await foreach (ChatMessageContent content in chat.InvokeAsync())
            {
                this.WriteAgentChatMessage(content);
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
