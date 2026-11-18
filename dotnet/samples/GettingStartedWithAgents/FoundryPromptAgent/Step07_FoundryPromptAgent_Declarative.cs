// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace GettingStarted.FoundryPromptAgents;

/// <summary>
/// This example demonstrates how to declaratively create a <see cref="ChatCompletionAgent"/> that uses a Microsoft Foundry Prompt Agent.
/// </summary>
/// <remarks>
/// The YAML defines the Semantic Kernel agent: its name, instructions, and template inputs.
/// The Prompt Agent definition in the Foundry project holds the model and the tools.
/// </remarks>
public class Step07_FoundryPromptAgent_Declarative(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    private readonly ChatCompletionAgentFactory _factory = new();

    /// <summary>
    /// Demonstrates creating and using an agent from configuration with a Kernel.
    /// </summary>
    [Fact]
    public async Task FoundryPromptAgentWithKernel()
    {
        var text =
            """
            type: chat_completion_agent
            name: StoryAgent
            description: Story Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            """;

        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("StoryAgent", new DeclarativeAgentDefinition(DeploymentName));

        try
        {
            var agent = await this._factory.CreateAgentFromYamlAsync(text, new() { Kernel = this.CreateKernel(promptAgent) }, TestConfiguration.ConfigurationRoot);

            await InvokeAgentAsync(agent!, "Cats and Dogs");
        }
        finally
        {
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    /// <summary>
    /// Demonstrates creating and using an agent from configuration, with the code-interpreter tool on the Prompt Agent.
    /// </summary>
    [Fact]
    public async Task FoundryPromptAgentWithCodeInterpreter()
    {
        var text =
            """
            type: chat_completion_agent
            name: MyAgent
            description: My helpful agent.
            instructions: You are helpful agent.
            """;

        DeclarativeAgentDefinition definition = new(DeploymentName);
        definition.Tools.Add(
            ResponseTool.CreateCodeInterpreterTool(
                new CodeInterpreterToolContainer(
                    CodeInterpreterToolContainerConfiguration.CreateAutomaticContainerConfiguration())));
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("MyAgent", definition);

        try
        {
            var agent = await this._factory.CreateAgentFromYamlAsync(text, new() { Kernel = this.CreateKernel(promptAgent) }, TestConfiguration.ConfigurationRoot);

            await InvokeAgentAsync(agent!, "Could you please create a bar chart for the operating profit using the following data and provide the file to me? Company A: $1.2 million, Company B: $2.5 million, Company C: $3.0 million, Company D: $1.8 million");
        }
        finally
        {
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    /// <summary>
    /// Demonstrates using an existing Prompt Agent from configuration.
    /// </summary>
    [Fact]
    public async Task FoundryPromptAgentWithExistingAgent()
    {
        var text =
            """
            type: chat_completion_agent
            name: StoryAgent
            instructions: Tell a story suitable for children about the topic provided by the user.
            """;

        // Create a Prompt Agent to represent one that already exists in the Foundry project.
        ProjectsAgentVersion createdAgent =
            await this.CreatePromptAgentAsync(
                "StoryAgent",
                new DeclarativeAgentDefinition(DeploymentName) { Instructions = "You always respond in French." });

        try
        {
            // Retrieve the existing Prompt Agent by name and version.
            ProjectsAgentVersion promptAgent = await this.Client.AgentAdministrationClient.GetAgentVersionAsync(createdAgent.Name, createdAgent.Version);

            var agent = await this._factory.CreateAgentFromYamlAsync(text, new() { Kernel = this.CreateKernel(promptAgent) }, TestConfiguration.ConfigurationRoot);

            await InvokeAgentAsync(agent!, "Cats and Dogs");
        }
        finally
        {
            await this.DeletePromptAgentAsync(createdAgent);
        }
    }

    /// <summary>
    /// Demonstrates creating and using an agent from configuration with templated instructions.
    /// </summary>
    [Fact]
    public async Task FoundryPromptAgentWithTemplate()
    {
        var text =
            """
            type: chat_completion_agent
            name: StoryAgent
            description: A agent that generates a story about a topic.
            instructions: Tell a story about {{$topic}} that is {{$length}} sentences long.
            inputs:
                topic:
                    description: The topic of the story.
                    required: true
                    default: Cats
                length:
                    description: The number of sentences in the story.
                    required: true
                    default: 2
            outputs:
                output1:
                    description: output1 description
            template:
                format: semantic-kernel
            """;

        // Semantic Kernel renders the templated instructions on every invocation, so the Prompt Agent definition has none.
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("StoryAgent", new DeclarativeAgentDefinition(DeploymentName));

        try
        {
            var agent = await this._factory.CreateAgentFromYamlAsync(
                text,
                new() { Kernel = this.CreateKernel(promptAgent), PromptTemplateFactory = new KernelPromptTemplateFactory() },
                TestConfiguration.ConfigurationRoot);
            Assert.NotNull(agent);

            var options = new AgentInvokeOptions()
            {
                KernelArguments = new()
                {
                    { "topic", "Dogs" },
                    { "length", "3" },
                }
            };

            await foreach (var response in agent.InvokeAsync(Array.Empty<ChatMessageContent>(), thread: null, options))
            {
                this.WriteAgentChatMessage(response);
            }
        }
        finally
        {
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }

    #region private
    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(Agent agent, string input)
    {
        await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, input)))
        {
            this.WriteAgentChatMessage(response);
            await this.DownloadGeneratedFilesAsync(response);
        }
    }
    #endregion
}
