// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Agents;
using Microsoft.SemanticKernel.Experimental.Agents.Chat;
using Microsoft.SemanticKernel.Experimental.Agents.Gpt;
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

        // Call the common chat-loop
        await ChatAsync(
            agent,
            "Fortune favors the bold.",
            "I came, I saw, I conquered.",
            "Practice makes perfect.");
    }

    /// <summary>
    /// Demonstrate single chat agent.
    /// </summary>
    [Fact]
    public async Task RunChatDualAgentsAsync()
    {
        WriteLine("======== Run:Dual Chat Agents ========");

        var agent1 = CreateChatAgent("Optimistic", "Evaluate the user input with optimism.");
        var agent2 = CreateChatAgent("Pessimistic", "Evaluate the user input with optimism.");

        await RunDualAgentAsync(agent1, agent2, "I think I'm going to do something really important today!");
    }

    /// <summary>
    /// Demonstrate single chat agent.
    /// </summary>
    [Fact]
    public async Task RunGptSingleAgentAsync()
    {
        WriteLine("======== Run:Single GPT Agent ========");

        var agent =
            await CreateGptAgentAsync(
                "Parrot",
                "Repeat the user message in the voice of a pirate and then end with a parrot sound.");

        // Call the common chat-loop
        await ChatAsync(
            agent,
            "Fortune favors the bold.",
            "I came, I saw, I conquered.",
            "Practice makes perfect.");
    }

    /// <summary>
    /// Demonstrate single chat agent.
    /// </summary>
    [Fact]
    public async Task RunGptDualAgentsAsync()
    {
        WriteLine("======== Run:Dual GPT Agents ========");

        var agent1 = await CreateGptAgentAsync("Optimistic", "Evaluate the user input with optimism.");
        var agent2 = await CreateGptAgentAsync("Pessimistic", "Evaluate the user input with optimism.");

        await RunDualAgentAsync(agent1, agent2, "I think I'm going to do something really important today!");
    }

    /// <summary>
    /// Demonstrate single chat agent.
    /// </summary>
    [Fact]
    public async Task RunMixedDualAgentsAsync()
    {
        WriteLine("======== Run:Dual GPT Agents ========");

        var agent1 = CreateChatAgent("Optimistic", "Evaluate the user input with optimism.");
        var agent2 = await CreateGptAgentAsync("Pessimistic", "Evaluate the user input with optimism.");

        await RunDualAgentAsync(agent1, agent2, "I think I'm going to do something really important today!");
    }

    private async Task<GptAgent> CreateGptAgentAsync(string name, string instructions)
    {
        return
            await GptAgent.CreateAsync(
                CreateKernel(),
                GetApiKey(),
                instructions,
                description: null,
                name);
    }

    private ChatAgent CreateChatAgent(string name, string instructions)
    {
        return
            new ChatAgent(
                CreateKernel(),
                instructions,
                description: null,
                name);
    }

    private async Task RunSingleAgentAsync(KernelAgent agent)
    {
        // Call the common chat-loop
        await ChatAsync(
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
            this.WriteLine($"# {content.Role}: {content.Content}");
        }
    }

    private Kernel CreateKernel()
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
