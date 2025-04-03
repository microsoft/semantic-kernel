// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;
using Amazon.BedrockAgentRuntime;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class BedrockAgentTests : IDisposable
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<BedrockAgentTests>()
        .Build();

    private readonly AmazonBedrockAgentClient _client = new();

    private readonly AmazonBedrockAgentRuntimeClient _runtimeClient = new();

    /// <summary>
    /// Integration test for invoking a <see cref="BedrockAgent"/>.
    /// </summary>
    [Theory(Skip = "This test is for manual verification.")]
    [InlineData("Why is the sky blue in one sentence?")]
    public async Task InvokeTestAsync(string input)
    {
        var agentModel = await this._client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest());
        var bedrockAgent = new BedrockAgent(agentModel, this._client, this._runtimeClient);
        var thread = new BedrockAgentThread(this._runtimeClient);

        try
        {
            await this.ExecuteAgentAsync(bedrockAgent, input, thread);
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
            await thread.DeleteAsync();
        }
    }

    /// <summary>
    /// Integration test for invoking a <see cref="BedrockAgent"/> with streaming.
    /// </summary>
    [Theory(Skip = "This test is for manual verification.")]
    [InlineData("Why is the sky blue in one sentence?")]
    public async Task InvokeStreamingTestAsync(string input)
    {
        var agentModel = await this._client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest());
        var bedrockAgent = new BedrockAgent(agentModel, this._client, this._runtimeClient);
        var thread = new BedrockAgentThread(this._runtimeClient);

        try
        {
            await this.ExecuteAgentStreamingAsync(bedrockAgent, input, thread);
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
            await thread.DeleteAsync();
        }
    }

    /// <summary>
    /// Integration test for invoking a <see cref="BedrockAgent"/> with code interpreter.
    /// </summary>
    [Theory(Skip = "This test is for manual verification.")]
    [InlineData(@"Create a bar chart for the following data:
Panda   5
Tiger   8
Lion    3
Monkey  6
Dolphin  2")]
    public async Task InvokeWithCodeInterpreterTestAsync(string input)
    {
        var agentModel = await this._client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest());
        var bedrockAgent = new BedrockAgent(agentModel, this._client, this._runtimeClient);
        await bedrockAgent.CreateCodeInterpreterActionGroupAsync();
        var thread = new BedrockAgentThread(this._runtimeClient);

        try
        {
            var responses = await this.ExecuteAgentAsync(bedrockAgent, input, thread);
            BinaryContent? binaryContent = null;
            foreach (var response in responses)
            {
                if (binaryContent == null && response.Items.Count > 0)
                {
                    binaryContent = response.Items.OfType<BinaryContent>().FirstOrDefault();
                }
            }
            Assert.NotNull(binaryContent);
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
            await thread.DeleteAsync();
        }
    }

    /// <summary>
    /// Integration test for invoking a <see cref="BedrockAgent"/> with Kernel functions.
    /// </summary>
    [Theory(Skip = "This test is for manual verification.")]
    [InlineData("What is the current weather in Seattle and what is the weather forecast in Seattle?", "weather")]
    public async Task InvokeWithKernelFunctionTestAsync(string input, string expected)
    {
        Kernel kernel = new();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());

        var agentModel = await this._client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest());
        var bedrockAgent = new BedrockAgent(agentModel, this._client, this._runtimeClient)
        {
            Kernel = kernel,
        };
        await bedrockAgent.CreateKernelFunctionActionGroupAsync();
        var thread = new BedrockAgentThread(this._runtimeClient);

        try
        {
            await this.ExecuteAgentAsync(bedrockAgent, input, thread, expected);
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
            await thread.DeleteAsync();
        }
    }

    /// <summary>
    /// Integration test for invoking a <see cref="BedrockAgent"/> with Kernel functions that return complex types.
    /// </summary>
    [Theory(Skip = "This test is for manual verification.")]
    [InlineData("What is the special soup and how much does it cost?", "Clam Chowder")]
    public async Task InvokeWithKernelFunctionTestComplexTypesAsync(string input, string expected)
    {
        Kernel kernel = new();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<MenuPlugin>());

        var agentModel = await this._client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest());
        var bedrockAgent = new BedrockAgent(agentModel, this._client, this._runtimeClient)
        {
            Kernel = kernel,
        };
        await bedrockAgent.CreateKernelFunctionActionGroupAsync();
        var thread = new BedrockAgentThread(this._runtimeClient);

        try
        {
            await this.ExecuteAgentAsync(bedrockAgent, input, thread, expected);
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
            await thread.DeleteAsync();
        }
    }

    /// <summary>
    /// Executes a <see cref="BedrockAgent"/> with the specified input and expected output.
    /// The output of the agent will be verified against the expected output.
    /// If the expected output is not provided, the verification will pass as long as the output is not null or empty.
    /// </summary>
    /// <param name="agent">The agent to execute.</param>
    /// <param name="input">The input to provide to the agent.</param>
    /// <param name="thread">The thread to use for the agent.</param>
    /// <param name="expected">The expected output from the agent.</param>
    /// <returns>The chat messages returned by the agent for additional verification.</returns>
    private async Task<List<ChatMessageContent>> ExecuteAgentAsync(BedrockAgent agent, string input, AgentThread thread, string? expected = null)
    {
        var responses = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, input), thread, null, default);
        string responseContent = string.Empty;
        List<ChatMessageContent> chatMessages = new();
        await foreach (ChatMessageContent response in responses)
        {
            // Non-streaming invoke will only return one response.
            responseContent = response.Content ?? string.Empty;
            chatMessages.Add(response);
        }

        if (expected != null)
        {
            Assert.Contains(expected, responseContent);
        }
        else
        {
            Assert.False(string.IsNullOrEmpty(responseContent));
        }

        return chatMessages;
    }

    /// <summary>
    /// Executes a <see cref="BedrockAgent"/> with the specified input and expected output using streaming.
    /// The output of the agent will be verified against the expected output.
    /// If the expected output is not provided, the verification will pass as long as the output is not null or empty.
    /// </summary>
    /// <param name="agent">The agent to execute.</param>
    /// <param name="input">The input to provide to the agent.</param>
    /// <param name="thread">The thread to use for the agent.</param>
    /// <param name="expected">The expected output from the agent.</param>
    /// <returns>The chat messages returned by the agent for additional verification.</returns>
    private async Task<List<StreamingChatMessageContent>> ExecuteAgentStreamingAsync(BedrockAgent agent, string input, AgentThread thread, string? expected = null)
    {
        var responses = agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, input), thread, null, default);
        string responseContent = string.Empty;
        List<StreamingChatMessageContent> chatMessages = new();
        await foreach (StreamingChatMessageContent response in responses)
        {
            responseContent = response.Content ?? string.Empty;
            chatMessages.Add(response);
        }

        if (expected != null)
        {
            Assert.Contains(expected, responseContent);
        }
        else
        {
            Assert.False(string.IsNullOrEmpty(responseContent));
        }

        return chatMessages;
    }

    private const string AgentName = "SKIntegrationTestAgent";
    private const string AgentDescription = "A helpful assistant who helps users find information.";
    private const string AgentInstruction = "You're a helpful assistant who helps users find information.";
    private CreateAgentRequest GetCreateAgentRequest()
    {
        BedrockAgentConfiguration bedrockAgentSettings = this._configuration.GetSection("BedrockAgent").Get<BedrockAgentConfiguration>()!;
        Assert.NotNull(bedrockAgentSettings);

        return new()
        {
            AgentName = $"{AgentName}-{Guid.NewGuid():n}",
            Description = AgentDescription,
            Instruction = AgentInstruction,
            AgentResourceRoleArn = bedrockAgentSettings.AgentResourceRoleArn,
            FoundationModel = bedrockAgentSettings.FoundationModel,
        };
    }

    public void Dispose()
    {
        this._client.Dispose();
        this._runtimeClient.Dispose();
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class WeatherPlugin
    {
        [KernelFunction, Description("Provides realtime weather information.")]
        public string Current([Description("The location to get the weather for.")] string location)
        {
            return $"The current weather in {location} is 72 degrees.";
        }

        [KernelFunction, Description("Forecast weather information.")]
        public string Forecast([Description("The location to get the weather for.")] string location)
        {
            return $"The forecast for {location} is 75 degrees tomorrow.";
        }
    }

    private sealed class MenuPlugin
    {
        [KernelFunction, Description("Provides a list of specials from the menu.")]
        public MenuItem[] GetSpecials()
        {
            return [.. s_menuItems.Where(i => i.IsSpecial)];
        }

        [KernelFunction, Description("Provides the price of the requested menu item.")]
        public float? GetItemPrice([Description("The name of the menu item.")] string menuItem)
        {
            return s_menuItems.FirstOrDefault(i => i.Name.Equals(menuItem, StringComparison.OrdinalIgnoreCase))?.Price;
        }

        private static readonly MenuItem[] s_menuItems =
        [
            new()
            {
                Category = "Soup",
                Name = "Clam Chowder",
                Price = 4.95f,
                IsSpecial = true,
            },
            new()
            {
                Category = "Soup",
                Name = "Tomato Soup",
                Price = 4.95f,
                IsSpecial = false,
            },
            new()
            {
                Category = "Salad",
                Name = "Cobb Salad",
                Price = 9.99f,
            },
            new()
            {
                Category = "Drink",
                Name = "Chai Tea",
                Price = 2.95f,
                IsSpecial = true,
            },
        ];

        public sealed class MenuItem
        {
            public required string Category { get; init; }
            public required string Name { get; init; }
            public float Price { get; init; }
            public bool IsSpecial { get; init; }
        }
    }
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
}
