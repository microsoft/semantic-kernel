// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Agents;
using Microsoft.SemanticKernel.Experimental.Agents.Chat;
using Microsoft.SemanticKernel.Experimental.Agents.Gpt;
using Plugins;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// $$$
/// </summary>
public class Example99_Agents : BaseTest
{
    /// <summary>
    /// Demonstrate single chat agent.
    /// </summary>
    [Fact]
    public async Task RunChatSingleAgentAsync()
    {
        WriteLine("======== Run:Single Chat Agent ========");

        var agent =
            CreateChatAgent(
                "Parrot",
                "Repeat the user message in the voice of a pirate and then end with a parrot sound.");

        await RunSingleAgentAsync(agent);
    }

    /// <summary>
    /// Demonstrate single chat agent.
    /// </summary>
    [Fact]
    public async Task RunChatDualAgentsAsync()
    {
        WriteLine("======== Run:Dual Chat Agents ========");

        var agent1 = CreateChatAgent("Optimistic", "Respond with optimism.");
        var agent2 = CreateChatAgent("Pessimistic", "Respond with extreme skeptism...don't be polite.");

        await RunDualAgentAsync(agent1, agent2, "I think I'm going to do something really important today!");
    }

    /// <summary>
    /// Demonstrate tooled chat agent.
    /// </summary>
    [Fact]
    public async Task RunChatToolsAgentAsync()
    {
        WriteLine("======== Run:Tooled Chat Agent ========");

        var plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        var agent =
            CreateChatAgent(
                "Host",
                "Use tools to answer questions about menu.",
                plugin);

        await RunToolAgentAsync(agent);
    }

    /// <summary>
    /// Demonstrate single gpt agent.
    /// </summary>
    [Fact]
    public async Task RunGptSingleAgentAsync()
    {
        WriteLine("======== Run:Single GPT Agent ========");

        var agent =
            await CreateGptAgentAsync(
                "Parrot",
                "Repeat the user message in the voice of a pirate and then end with a parrot sound.");

        await RunSingleAgentAsync(agent);
    }

    /// <summary>
    /// Demonstrate single gpt agent.
    /// </summary>
    [Fact]
    public async Task RunGptDualAgentsAsync()
    {
        WriteLine("======== Run:Dual GPT Agents ========");

        var agent1 = await CreateGptAgentAsync("Optimistic", "Evaluate the user input with optimism.");
        var agent2 = await CreateGptAgentAsync("Pessimistic", "Respond with extreme skeptism...don't be polite.");

        await RunDualAgentAsync(agent1, agent2, "I think I'm going to do something really important today!");
    }

    /// <summary>
    /// Demonstrate tooled gpt agent.
    /// </summary>
    [Fact]
    public async Task RunGptToolsAgentAsync()
    {
        WriteLine("======== Run:Tooled GPT Agent ========");

        var plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        var agent =
            await CreateGptAgentAsync(
                "Host",
                "Use tools to answer questions about menu.",
                plugin);

        await RunToolAgentAsync(agent);
    }

    /// <summary>
    /// Demonstrate mixed agents.
    /// </summary>
    [Fact]
    public async Task RunMixedAgentsAsync()
    {
        WriteLine("======== Run:Dual GPT Agents ========");

        var agent1 = CreateChatAgent("Optimistic", "Respond with optimism.");
        var agent2 = await CreateGptAgentAsync("Pessimistic", "Respond with extreme skeptism...don't be polite.");

        await RunDualAgentAsync(agent1, agent2, "I think I'm going to do something really important today!");
    }

    private async Task<GptAgent> CreateGptAgentAsync(string name, string instructions, KernelPlugin? plugin = null)
    {
        return
            await GptAgent.CreateAsync(
                CreateKernel(plugin),
                GetApiKey(),
                instructions,
                description: null,
                name);
    }

    private ChatAgent CreateChatAgent(string name, string instructions, KernelPlugin? plugin = null)
    {
        return
            new ChatAgent(
                CreateKernel(plugin),
                instructions,
                description: null,
                name);
    }

    private Task RunSingleAgentAsync(KernelAgent agent)
    {
        return
            ChatAsync(
                agent,
                "Fortune favors the bold.",
                "I came, I saw, I conquered.",
                "Practice makes perfect.");
    }

    private async Task RunDualAgentAsync(KernelAgent agent1, KernelAgent agent2, string input)
    {
        var nexus = new ManualNexus(); // $$$

        await InvokeAgentAsync(nexus, agent1, input); // $$$ USER PROXY
        await InvokeAgentAsync(nexus, agent2);
    }


    private Task RunToolAgentAsync(KernelAgent agent)
    {
        return
            ChatAsync(
                agent,
                "What is the special soup?",
                "What is the special drink?",
                "What else is on the menu?");
    }

    /// <summary>
    /// Common chat loop.
    /// </summary>
    private async Task ChatAsync(
        KernelAgent agent,
        params string[] messages)
    {
        var nexus = new ManualNexus(); // $$$

        this.WriteLine($"[{agent.Id}]");

        // Process each user message and agent response.
        foreach (var message in messages)
        {
            await InvokeAgentAsync(nexus, agent, message);
        }
    }

    private async Task InvokeAgentAsync(ManualNexus nexus, KernelAgent agent, string? message = null)
    {
        var response = await nexus.InvokeAsync(agent, message);
        foreach (var content in response)
        {
            //this.WriteLine($"[{content.Id}]"); $$$
            this.WriteLine($"# {content.Role}: '{content.Content}'");
        }
    }

    private Kernel CreateKernel(KernelPlugin? plugin = null)
    {
        var builder = Kernel.CreateBuilder();

        if (string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint))
        {
            builder.AddOpenAIChatCompletion(
                TestConfiguration.OpenAI.ChatModelId,
                TestConfiguration.OpenAI.ApiKey);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);
        }

        if (plugin != null)
        {
            builder.Plugins.Add(plugin);
        }

        return builder.Build();
    }

    private string GetApiKey()
    {
        if (string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint))
        {
            return TestConfiguration.OpenAI.ApiKey;
        }

        return TestConfiguration.AzureOpenAI.ApiKey;
    }

    public Example99_Agents(ITestOutputHelper output) : base(output)
    {
    }
}
