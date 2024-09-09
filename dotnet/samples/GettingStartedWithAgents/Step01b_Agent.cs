// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace GettingStarted;

/// <summary>
/// %%%
/// </summary>
public class Step01b_Agent(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task UseSingleChatCompletionAgentAsync()
    {
        // Define the agent
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        Kernel kernel = this.CreateKernelWithChatCompletion();
        ChatCompletionAgent agent = kernel.CreateChatCompletionAgentFromPromptYaml(generateStoryYaml);

        /// Create the chat history to capture the agent interaction.
        ChatHistory chat = [];

        // Respond to user input
        await InvokeAgentAsync(
            new()
            {
                { "topic", "Dog" },
                { "length", "3" },
            });

        await InvokeAgentAsync(
            new()
            {
                { "topic", "Cat" },
                { "length", "3" },
            });

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(KernelArguments arguments)
        {
            await foreach (ChatMessageContent content in agent.InvokeAsync(chat, arguments))
            {
                chat.Add(content);

                Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }
    }
}
