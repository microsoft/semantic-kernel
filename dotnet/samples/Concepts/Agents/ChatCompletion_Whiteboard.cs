// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Memory;

namespace Agents;

#pragma warning disable SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// adding whiteboarding capabilities, where the most relevant information from the conversation is captured on a whiteboard.
/// This is useful for long running conversations where the conversation history may need to be truncated
/// over time, but you do not want to agent to lose context.
/// </summary>
public class ChatCompletion_Whiteboard(ITestOutputHelper output) : BaseTest(output)
{
    private const string AgentName = "FriendlyAssistant";
    private const string AgentInstructions = "You are a friendly assistant";

    /// <summary>
    /// Shows how to allow an agent to use a whiteboard for storing the most important information
    /// from a long running, truncated conversation.
    /// </summary>
    [Fact]
    private async Task UseWhiteboardForShortTermMemory()
    {
        var chatClient = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAI.Endpoint), new AzureCliCredential())
            .GetChatClient(TestConfiguration.AzureOpenAI.ChatDeploymentName)
            .AsIChatClient();

        // Create the whiteboard.
        var whiteboardProvider = new WhiteboardProvider(chatClient);

        // Create our agent and add our finance plugin with auto function invocation.
        Kernel kernel = this.CreateKernelWithChatCompletion();

        // Create the agent with our sample plugin.
        kernel.Plugins.AddFromType<VMPlugin>();
        ChatCompletionAgent agent =
            new()
            {
                Name = AgentName,
                Instructions = AgentInstructions,
                Kernel = kernel,
                Arguments = new KernelArguments(new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() })
            };

        // Create a chat history reducer that we can use to truncate the chat history
        // when it goes over 3 items.
        var chatHistoryReducer = new ChatHistoryTruncationReducer(3, 3);

        // Create a thread for the agent and add the whiteboard to it.
        ChatHistoryAgentThread agentThread = new();
        agentThread.AIContextProviders.Add(whiteboardProvider);

        // Simulate a conversation with the agent.
        // We will also truncate the conversation once it goes over a few items.
        await InvokeWithConsoleWriteLine("Hello");
        await InvokeWithConsoleWriteLine("I'd like to create a VM?");
        await InvokeWithConsoleWriteLine("I want it to have 3 cores.");
        await InvokeWithConsoleWriteLine("I want it to have 48GB of RAM.");
        await InvokeWithConsoleWriteLine("I want it to have a 500GB Harddrive.");
        await InvokeWithConsoleWriteLine("I want it in Europe.");
        await InvokeWithConsoleWriteLine("Can you make it Linux and call it 'ContosoVM'.");
        await InvokeWithConsoleWriteLine("OK, let's call it `ContosoFinanceVM_Europe` instead.");
        await InvokeWithConsoleWriteLine("Thanks, now I want to create another VM.");
        await InvokeWithConsoleWriteLine("Make all the options the same as the last one, except for the region, which should be North America, and the name, which should be 'ContosoFinanceVM_NorthAmerica'.");

        async Task InvokeWithConsoleWriteLine(string message)
        {
            // Print the user input.
            Console.WriteLine($"User: {message}");

            // Invoke the agent.
            ChatMessageContent response = await agent.InvokeAsync(message, agentThread).FirstAsync();

            // Print the response.
            Console.WriteLine($"Assistant:\n{response.Content}\n");

            // Make sure any async whiteboard processing is complete before we print out its contents.
            await whiteboardProvider.WhenProcessingCompleteAsync();

            // Print out the whiteboard contents.
            Console.WriteLine("Whiteboard contents:");
            foreach (var item in whiteboardProvider.CurrentWhiteboardContent)
            {
                Console.WriteLine($"- {item}");
            }
            Console.WriteLine();

            // Truncate the chat history if it gets too big.
            await agentThread.ChatHistory.ReduceInPlaceAsync(chatHistoryReducer, CancellationToken.None);
        }
    }

    private sealed class VMPlugin
    {
        [KernelFunction]
        public Task<VMCreateResult> CreateVM(Region region, OperatingSystem os, string name, int numberOfCores, int memorySizeInGB, int hddSizeInGB)
        {
            if (name == "ContosoVM")
            {
                throw new Exception("VM name already exists");
            }

            return Task.FromResult(new VMCreateResult { VMId = Guid.NewGuid().ToString() });
        }
    }

    public class VMCreateResult
    {
        public string VMId { get; set; } = string.Empty;
    }

    private enum Region
    {
        NorthAmerica,
        SouthAmerica,
        Europe,
        Asia,
        Africa,
        Australia
    }

    private enum OperatingSystem
    {
        Windows,
        Linux,
        MacOS
    }
}
