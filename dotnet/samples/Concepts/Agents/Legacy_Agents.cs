// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Agents;
using Plugins;
using Resources;

namespace Agents;

/// <summary>
/// Showcase Open AI Agent integration with semantic kernel:
/// https://platform.openai.com/docs/api-reference/agents
/// </summary>
public class Legacy_Agents(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Chat using the "Parrot" agent.
    /// Tools/functions: None
    /// </summary>
    [Fact]
    public Task RunSimpleChatAsync()
    {
        Console.WriteLine("======== Run:SimpleChat ========");

        // Call the common chat-loop
        return ChatAsync(
            "Agents.ParrotAgent.yaml", // Defined under ./Resources/Agents
            plugin: null, // No plugin
            arguments: new KernelArguments { { "count", 3 } },
            "Fortune favors the bold.",
            "I came, I saw, I conquered.",
            "Practice makes perfect.");
    }

    /// <summary>
    /// Chat using the "Tool" agent and a method function.
    /// Tools/functions: MenuPlugin
    /// </summary>
    [Fact]
    public async Task RunWithMethodFunctionsAsync()
    {
        Console.WriteLine("======== Run:WithMethodFunctions ========");

        LegacyMenuPlugin menuApi = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(menuApi);

        // Call the common chat-loop
        await ChatAsync(
            "Agents.ToolAgent.yaml", // Defined under ./Resources/Agents
            plugin,
            arguments: null,
            "Hello",
            "What is the special soup?",
            "What is the special drink?",
            "Do you have enough soup for 5 orders?",
            "Thank you!");
    }

    /// <summary>
    /// Chat using the "Tool" agent and a prompt function.
    /// Tools/functions: spellChecker prompt function
    /// </summary>
    [Fact]
    public Task RunWithPromptFunctionsAsync()
    {
        Console.WriteLine("======== WithPromptFunctions ========");

        // Create a prompt function.
        var function = KernelFunctionFactory.CreateFromPrompt(
             "Correct any misspelling or gramatical errors provided in input: {{$input}}",
              functionName: "spellChecker",
              description: "Correct the spelling for the user input.");

        var plugin = KernelPluginFactory.CreateFromFunctions("spelling", "Spelling functions", [function]);

        // Call the common chat-loop
        return ChatAsync(
            "Agents.ToolAgent.yaml", // Defined under ./Resources/Agents
            plugin,
            arguments: null,
            "Hello",
            "Is this spelled correctly: exercize",
            "What is the special soup?",
            "Thank you!");
    }

    /// <summary>
    /// Invoke agent just like any other <see cref="KernelFunction"/>.
    /// </summary>
    [Fact]
    public async Task RunAsFunctionAsync()
    {
        Console.WriteLine("======== Run:AsFunction ========");

        // Create parrot agent, same as the other cases.
        var agent =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
                .FromTemplate(EmbeddedResource.Read("Agents.ParrotAgent.yaml"))
                .BuildAsync();

        try
        {
            // Invoke agent plugin.
            var response = await agent.AsPlugin().InvokeAsync("Practice makes perfect.", new KernelArguments { { "count", 2 } });

            // Display result.
            Console.WriteLine(response ?? $"No response from agent: {agent.Id}");
        }
        finally
        {
            // Clean-up (storage costs $)
            await agent.DeleteAsync();
        }
    }

    /// <summary>
    /// Common chat loop used for: RunSimpleChatAsync, RunWithMethodFunctionsAsync, and RunWithPromptFunctionsAsync.
    /// 1. Reads agent definition from"resourcePath" parameter.
    /// 2. Initializes agent with definition and the specified "plugin".
    /// 3. Display the agent identifier
    /// 4. Create a chat-thread
    /// 5. Process the provided "messages" on the chat-thread
    /// </summary>
    private async Task ChatAsync(
        string resourcePath,
        KernelPlugin? plugin = null,
        KernelArguments? arguments = null,
        params string[] messages)
    {
        // Read agent resource
        var definition = EmbeddedResource.Read(resourcePath);

        // Create agent
        var agent =
            await CreateAgentBuilder()
                .FromTemplate(definition)
                .WithPlugin(plugin)
                .BuildAsync();

        // Create chat thread.  Note: Thread is not bound to a single agent.
        var thread = await agent.NewThreadAsync();

        // Enable provided arguments to be passed to function-calling
        thread.EnableFunctionArgumentPassThrough = true;

        try
        {
            // Display agent identifier.
            Console.WriteLine($"[{agent.Id}]");

            // Process each user message and agent response.
            foreach (var response in messages.Select(m => thread.InvokeAsync(agent, m, arguments)))
            {
                await foreach (var message in response)
                {
                    Console.WriteLine($"[{message.Id}]");
                    Console.WriteLine($"# {message.Role}: {message.Content}");
                }
            }
        }
        finally
        {
            // Clean-up (storage costs $)
            await Task.WhenAll(
                thread?.DeleteAsync() ?? Task.CompletedTask,
                agent.DeleteAsync());
        }
    }

    private AgentBuilder CreateAgentBuilder()
    {
        return
            this.ForceOpenAI || string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint) ?
                new AgentBuilder().WithOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey) :
                new AgentBuilder().WithAzureOpenAIChatCompletion(TestConfiguration.AzureOpenAI.Endpoint, TestConfiguration.AzureOpenAI.ChatDeploymentName, TestConfiguration.AzureOpenAI.ApiKey);
    }
}
