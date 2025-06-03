// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to interact with a <see cref="BedrockAgent"/> with kernel functions.
/// </summary>
public class Step03_BedrockAgent_Functions(ITestOutputHelper output) : BaseBedrockAgentTest(output)
{
    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> with kernel functions enabled and interact with it.
    /// The agent will respond to the user query by calling kernel functions to provide weather information.
    /// </summary>
    [Fact]
    public async Task UseAgentWithFunctions()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions");

        // Respond to user input
        try
        {
            var responses = bedrockAgent.InvokeAsync(
                new ChatMessageContent(AuthorRole.User, "What is the weather in Seattle?"),
                null);
            await foreach (ChatMessageContent response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> with kernel functions enabled and interact with it.
    /// The agent will respond to the user query by calling kernel functions that returns complex types to provide
    /// information about the menu.
    /// </summary>
    [Fact]
    public async Task UseAgentWithFunctionsComplexType()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions_Complex_Types");

        // Respond to user input
        try
        {
            var responses = bedrockAgent.InvokeAsync(
                 new ChatMessageContent(AuthorRole.User, "What is the special soup and how much does it cost?"),
                null);
            await foreach (ChatMessageContent response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> with kernel functions enabled and interact with it using streaming.
    /// The agent will respond to the user query by calling kernel functions to provide weather information.
    /// </summary>
    [Fact]
    public async Task UseAgentStreamingWithFunctions()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions_Streaming");

        // Respond to user input
        try
        {
            var streamingResponses = bedrockAgent.InvokeStreamingAsync(
                new ChatMessageContent(AuthorRole.User, "What is the weather forecast in Seattle?"),
                null);
            await foreach (StreamingChatMessageContent response in streamingResponses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    /// <summary>
    /// Demonstrates how to create a new <see cref="BedrockAgent"/> with kernel functions enabled and interact with it.
    /// The agent will respond to the user query by calling multiple kernel functions in parallel to provide weather information.
    /// </summary>
    [Fact]
    public async Task UseAgentWithParallelFunctionsAsync()
    {
        // Create the agent
        var bedrockAgent = await this.CreateAgentAsync("Step03_BedrockAgent_Functions_Parallel");

        // Respond to user input
        try
        {
            var responses = bedrockAgent.InvokeAsync(
                new ChatMessageContent(AuthorRole.User, "What is the current weather in Seattle and what is the weather forecast in Seattle?"),
                null);
            await foreach (ChatMessageContent response in responses)
            {
                if (response.Content != null)
                {
                    this.Output.WriteLine(response.Content);
                }
            }
        }
        finally
        {
            await bedrockAgent.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
        }
    }

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        // Create a new agent on the Bedrock Agent service and prepare it for use
        var agentModel = await this.Client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest(agentName));
        // Create a new kernel with plugins
        Kernel kernel = new();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<MenuPlugin>());
        // Create a new BedrockAgent instance with the agent model and the client
        // so that we can interact with the agent using Semantic Kernel contents.
        var bedrockAgent = new BedrockAgent(agentModel, this.Client, this.RuntimeClient);
        // Create the kernel function action group and prepare the agent for interaction
        await bedrockAgent.CreateKernelFunctionActionGroupAsync();

        return bedrockAgent;
    }

    private sealed class WeatherPlugin
    {
        [KernelFunction, Description("Provides real-time weather information.")]
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
        [KernelFunction, Description("Get the menu.")]
        public MenuItem[] GetMenu()
        {
            return s_menuItems;
        }

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
            public string Category { get; init; }
            public string Name { get; init; }
            public float Price { get; init; }
            public bool IsSpecial { get; init; }
        }
    }
}
