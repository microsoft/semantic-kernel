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

    private const string JokerName = "Joker";
    private const string JokerInstructions = "You are good at telling jokes.";

    /// <summary>
    /// Demonstrate the usage of <see cref="ChatCompletionAgent"/> where each invocation is
    /// a unique interaction with no conversation history between them.
    /// </summary>
    [Fact]
    public async Task UseSingleChatCompletionAgent()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();

        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = ParrotName,
                Instructions = ParrotInstructions,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        // Respond to user input
        await InvokeAgentAsync("Fortune favors the bold.");
        await InvokeAgentAsync("I came, I saw, I conquered.");
        await InvokeAgentAsync("Practice makes perfect.");

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync(message))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }

    /// <summary>
    /// Demonstrate the usage of <see cref="ChatCompletionAgent"/> where a conversation history is maintained.
    /// </summary>
    [Fact]
    public async Task UseSingleChatCompletionAgentWithConversation()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();

        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = JokerName,
                Instructions = JokerInstructions,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        // Define a thread variable to maintain the conversation context.
        // Since we are passing a null thread to InvokeAsync on the first invocation,
        // the agent will create a new thread for the conversation.
        AgentThread? thread = null;

        // Respond to user input
        await InvokeAgentAsync("Tell me a joke about a pirate.");
        await InvokeAgentAsync("Now add some emojis to the joke.");

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync(message, thread))
            {
                this.WriteAgentChatMessage(response);
                thread = response.Thread;
            }
        }
    }

    /// <summary>
    /// Demonstrate the usage of <see cref="ChatCompletionAgent"/> where a conversation history is maintained
    /// and where the thread containing the conversation is created manually.
    /// </summary>
    [Fact]
    public async Task UseSingleChatCompletionAgentWithManuallyCreatedThread()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();

        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Name = JokerName,
                Instructions = JokerInstructions,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        // Define a thread variable to maintain the conversation context.
        // Since we are creating the thread, we can pass some initial messages to it.
        AgentThread? thread = new ChatHistoryAgentThread(
            [
                new ChatMessageContent(AuthorRole.User, "Tell me a joke about a pirate."),
                new ChatMessageContent(AuthorRole.Assistant, "Why did the pirate go to school? Because he wanted to improve his \"arrrrrrrrrticulation\""),
            ]);

        // Respond to user input
        await InvokeAgentAsync("Now add some emojis to the joke.");
        await InvokeAgentAsync("Now make the joke sillier.");

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            // Use the thread we created earlier to continue the conversation.
            await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync(message, thread))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }

    [Fact]
    public async Task UseTemplateForChatCompletionAgent()
    {
        // Define the agent
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);
        KernelPromptTemplateFactory templateFactory = new();

        // Instructions, Name and Description properties defined via the config.
        ChatCompletionAgent agent =
            new(templateConfig, templateFactory)
            {
                Kernel = this.CreateKernelWithChatCompletion(),
                Arguments = new()
                    {
                        { "topic", "Dog" },
                        { "length", "3" },
                    }
            };

        // Invoke the agent with the default arguments.
        await InvokeAgentAsync();

        // Invoke the agent with the override arguments.
        await InvokeAgentAsync(
            new()
            {
                { "topic", "Cat" },
                { "length", "3" },
            });

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(KernelArguments? arguments = null)
        {
            // Invoke the agent without any messages, since the agent has all that it needs via the template and arguments.
            await foreach (ChatMessageContent content in agent.InvokeAsync(options: new() { KernelArguments = arguments }))
            {
                WriteAgentChatMessage(content);
            }
        }
    }
}
