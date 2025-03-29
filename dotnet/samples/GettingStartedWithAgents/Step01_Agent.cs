// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace GettingStarted;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Step01_Agent(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string ParrotName = "Parrot";
    private const string ParrotInstructions = "Repeat the user message in the voice of a pirate and then end with a parrot sound.";

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseSingleChatCompletionAgent(bool useChatClient)
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();

        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = ParrotName,
                Instructions = ParrotInstructions,
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient),
            };

        /// Create the chat history to capture the agent interaction.
        ChatHistory chat = [];

        // Respond to user input
        await InvokeAgentAsync("Fortune favors the bold.");
        await InvokeAgentAsync("I came, I saw, I conquered.");
        await InvokeAgentAsync("Practice makes perfect.");

        chatClient?.Dispose();

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.Add(message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(chat))
            {
                chat.Add(response);

                this.WriteAgentChatMessage(response);
            }
        }
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task UseTemplateForChatCompletionAgent(bool useChatClient)
    {
        // Define the agent
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);
        KernelPromptTemplateFactory templateFactory = new();

        // Instructions, Name and Description properties defined via the config.
        ChatCompletionAgent agent =
            new(templateConfig, templateFactory)
            {
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient),
                Arguments =
                    {
                        { "topic", "Dog" },
                        { "length", "3" },
                    }
            };

        /// Create the chat history to capture the agent interaction.
        ChatHistory chat = [];

        // Invoke the agent with the default arguments.
        await InvokeAgentAsync();

        // Invoke the agent with the override arguments.
        await InvokeAgentAsync(
            new()
            {
                { "topic", "Cat" },
                { "length", "3" },
            });

        chatClient?.Dispose();

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(KernelArguments? arguments = null)
        {
            await foreach (ChatMessageContent content in agent.InvokeAsync(chat, arguments))
            {
                chat.Add(content);

                WriteAgentChatMessage(content);
            }
        }
    }
}
