// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Amazon.BedrockAgent;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.BedrockAgents;

/// <summary>
/// This example demonstrates how to declaratively create instances of <see cref="BedrockAgent"/>.
/// </summary>
public class Step07_BedrockAgent_Declarative : BaseBedrockAgentTest
{
    /// <summary>
    /// Demonstrates creating and using a Bedrock Agent with using configuration settings.
    /// </summary>
    [Fact]
    public async Task BedrockAgentWithConfiguration()
    {
        var text =
            """
            type: bedrock_agent
            name: StoryAgent
            description: Story Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: ${BedrockAgent:FoundationModel}
              connection:
                type: bedrock
                agent_resource_role_arn: ${BedrockAgent:AgentResourceRoleArn}
            """;
        BedrockAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, configuration: TestConfiguration.ConfigurationRoot);

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    /// <summary>
    /// Demonstrates loading an existing Bedrock Agent.
    /// </summary>
    [Fact]
    public async Task BedrockAgentWithId()
    {
        var text =
            """
            id: ${BedrockAgent:AgentId}
            type: bedrock_agent
            """;
        BedrockAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, configuration: TestConfiguration.ConfigurationRoot);

        await InvokeAgentAsync(agent!, "What is Semantic Kernel?", false);
    }

    /// <summary>
    /// Demonstrates creating and using a Bedrock Agent with a code interpreter.
    /// </summary>
    [Fact]
    public async Task BedrockAgentWithCodeInterpreter()
    {
        var text =
            """
            type: bedrock_agent
            name: CodeInterpreterAgent
            instructions: Use the code interpreter tool to answer questions which require code to be generated and executed.
            description: Agent with code interpreter tool.
            model:
              id: ${BedrockAgent:FoundationModel}
              connection:
                type: bedrock
                agent_resource_role_arn: ${BedrockAgent:AgentResourceRoleArn}
            tools:
              - type: code_interpreter
            """;
        BedrockAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel }, TestConfiguration.ConfigurationRoot);

        await InvokeAgentAsync(agent!, "Use code to determine the values in the Fibonacci sequence that are less then the value of 101?");
    }

    /// <summary>
    /// Demonstrates creating and using a Bedrock Agent with functions.
    /// </summary>
    [Fact]
    public async Task BedrockAgentWithFunctions()
    {
        var text =
            """
            type: bedrock_agent
            name: FunctionCallingAgent
            instructions: Use the provided functions to answer questions about the menu.
            description: This agent uses the provided functions to answer questions about the menu.
            model:
              id: ${BedrockAgent:FoundationModel}
              connection:
                type: bedrock
                agent_resource_role_arn: ${BedrockAgent:AgentResourceRoleArn}
            tools:
              - id: Current
                type: function
                description: Provides real-time weather information.
                options:
                  parameters:
                    - name: location
                      type: string
                      required: true
                      description: The location to get the weather for.
              - id: Forecast
                type: function
                description: Forecast weather information.
                options:
                  parameters:
                    - name: location
                      type: string
                      required: true
                      description: The location to get the weather for.  
            """;
        BedrockAgentFactory factory = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<WeatherPlugin>();
        this._kernel.Plugins.Add(plugin);

        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel }, TestConfiguration.ConfigurationRoot);

        await InvokeAgentAsync(agent!, "What is the current weather in Seattle and what is the weather forecast in Seattle?");
    }

    /// <summary>
    /// Demonstrates creating and using a Bedrock Agent with a knowledge base.
    /// </summary>
    [Fact]
    public async Task BedrockAgentWithKnowledgeBase()
    {
        var text =
            """
            type: bedrock_agent
            name: KnowledgeBaseAgent
            instructions: Use the provided knowledge base to answer questions.
            description: This agent uses the provided knowledge base to answer questions.
            model:
              id: ${BedrockAgent:FoundationModel}
              connection:
                type: bedrock
                agent_resource_role_arn: ${BedrockAgent:AgentResourceRoleArn}
            tools:
              - type: knowledge_base
                description: You will find information here.
                options:
                  knowledge_base_id: ${BedrockAgent:KnowledgeBaseId}
            """;
        BedrockAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel }, TestConfiguration.ConfigurationRoot);

        await InvokeAgentAsync(agent!, "What is Semantic Kernel?");
    }

    public Step07_BedrockAgent_Declarative(ITestOutputHelper output) : base(output)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<AmazonBedrockAgentClient>(this.Client);
        this._kernel = builder.Build();
    }

    protected override async Task<BedrockAgent> CreateAgentAsync(string agentName)
    {
        // Create a new agent on the Bedrock Agent service and prepare it for use
        var agentModel = await this.Client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest(agentName));
        // Create a new kernel with plugins
        Kernel kernel = new();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());
        // Create a new BedrockAgent instance with the agent model and the client
        // so that we can interact with the agent using Semantic Kernel contents.
        var bedrockAgent = new BedrockAgent(agentModel, this.Client, this.RuntimeClient)
        {
            Kernel = kernel,
        };
        // Create the kernel function action group and prepare the agent for interaction
        await bedrockAgent.CreateKernelFunctionActionGroupAsync();

        return bedrockAgent;
    }

    #region private
    private readonly Kernel _kernel;

    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(Agent agent, string input, bool deleteAgent = true)
    {
        AgentThread? agentThread = null;
        try
        {
            await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, input)))
            {
                agentThread = response.Thread;
                WriteAgentChatMessage(response);
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"Error invoking agent: {e.Message}");
        }
        finally
        {
            if (deleteAgent)
            {
                var bedrockAgent = agent as BedrockAgent;
                await bedrockAgent!.Client.DeleteAgentAsync(new() { AgentId = bedrockAgent.Id });
            }

            if (agentThread is not null)
            {
                await agentThread.DeleteAsync();
            }
        }
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
    #endregion
}
