// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;
/// <summary>
/// Demonstrate that serialization of <see cref="AgentGroupChat"/> in with a <see cref="ChatCompletionAgent"/> participant.
/// </summary>
public class ChatCompletion_Serialization(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string HostName = "Host";
    private const string HostInstructions = "Answer questions about the menu.";

    [Fact]
    public async Task SerializeAndRestoreAgentGroupChatAsync()
    {
        // Define the agent
        ChatCompletionAgent agent =
            new()
            {
                Instructions = HostInstructions,
                Name = HostName,
                Kernel = this.CreateKernelWithChatCompletion(),
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        // Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        AgentGroupChat chat = CreateGroupChat();

        // Invoke chat and display messages.
        Console.WriteLine("============= Dynamic Agent Chat - Primary (prior to serialization) ==============");
        await InvokeAgentAsync(chat, "Hello");
        await InvokeAgentAsync(chat, "What is the special soup?");

        AgentGroupChat copy = CreateGroupChat();
        Console.WriteLine("\n=========== Serialize and restore the Agent Chat into a new instance ============");
        await CloneChatAsync(chat, copy);

        Console.WriteLine("\n============ Continue with the dynamic Agent Chat (after deserialization) ===============");
        await InvokeAgentAsync(copy, "What is the special drink?");
        await InvokeAgentAsync(copy, "Thank you");

        Console.WriteLine("\n============ The entire Agent Chat (includes messages prior to serialization and those after deserialization) ==============");
        await foreach (ChatMessageContent content in copy.GetChatMessagesAsync())
        {
            this.WriteAgentChatMessage(content);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(AgentGroupChat chat, string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.AddChatMessage(message);

            this.WriteAgentChatMessage(message);

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

        AgentGroupChat CreateGroupChat() => new(agent);
    }

    private sealed class MenuPlugin
    {
        [KernelFunction, Description("Provides a list of specials from the menu.")]
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string GetSpecials() =>
            """
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            """;

        [KernelFunction, Description("Provides the price of the requested menu item.")]
        public string GetItemPrice(
            [Description("The name of the menu item.")]
            string menuItem) =>
            "$9.99";
    }
}
