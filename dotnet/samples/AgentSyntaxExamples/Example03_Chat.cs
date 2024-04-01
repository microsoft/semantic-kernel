// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// $$$
/// </summary>
public class Example03_Chat : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        //// Define the agent
        //ChatCompletionAgent agent =
        //    new(
        //        kernel: this.CreateKernelWithChatCompletion(),
        //        instructions: AgentInventory.HostInstructions)
        //    {
        //        ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }
        //    };

        //// Initialize plugin and add to the agent's Kernel (same as direct Kernel usage).
        //KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        //agent.Kernel.Plugins.Add(plugin);

        //// Create a nexus for agent interaction. For more, see: Example03_Chat.
        //var nexus = new TestChat();

        //// Respond to user input, invoking functions where appropriate.
        //await WriteAgentResponseAsync("Hello");
        //await WriteAgentResponseAsync("What is the special soup?");
        //await WriteAgentResponseAsync("What is the special drink?");
        //await WriteAgentResponseAsync("Thank you");

        //// Local function to invoke agent and display the conversation messages.
        //async Task WriteAgentResponseAsync(string input)
        //{
        //    await foreach (var content in nexus.InvokeAsync(agent, input))
        //    {
        //        this.WriteLine($"# {content.Role}: '{content.Content}'");
        //        //this.WriteLine($"# {content.Role} - {content.Name ?? "*"}: '{content.Content}'"); // $$$ IDENTITY
        //    }
        //}
    }

    public Example03_Chat(ITestOutputHelper output)
        : base(output)
    {
        // Nothing to do...
    }
}
