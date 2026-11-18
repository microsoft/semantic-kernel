// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;

namespace Agents;

/// <summary>
/// Demonstrate parameterized template instruction for an agent that uses a Microsoft Foundry Prompt Agent.
/// </summary>
/// <remarks>
/// The Prompt Agent definition is fixed when the version is created, so Semantic Kernel renders the
/// templated instructions on every invocation and sends them as a system message.
/// </remarks>
public class FoundryPromptAgent_Templating(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    private static readonly (string Input, string? Style)[] s_inputs =
        [
            (Input: "Home cooking is great.", Style: null),
            (Input: "Talk about world peace.", Style: "iambic pentameter"),
            (Input: "Say something about doing your best.", Style: "e. e. cummings"),
            (Input: "What do you think about having fun?", Style: "old school rap")
        ];

    [Fact]
    public async Task InvokeAgentWithInstructionsAsync()
    {
        // Define the Prompt Agent
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("Poet", new DeclarativeAgentDefinition(DeploymentName));

        // Create the agent
        ChatCompletionAgent agent =
            new()
            {
                Instructions =
                    """
                    Write a one verse poem on the requested topic in the styles of {{$style}}.
                    Always state the requested style of the poem.
                    """,
                Kernel = this.CreateKernel(promptAgent),
                Arguments = new()
                {
                    {"style", "haiku"}
                },
            };

        await InvokeAgentWithTemplateAsync(agent, promptAgent);
    }

    [Fact]
    public async Task InvokeAgentWithKernelTemplateAsync()
    {
        // Default factory is KernelPromptTemplateFactory
        await InvokeAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the styles of {{$style}}.
            Always state the requested style of the poem.
            """,
            PromptTemplateConfig.SemanticKernelTemplateFormat,
            new KernelPromptTemplateFactory());
    }

    [Fact]
    public async Task InvokeAgentWithHandlebarsTemplateAsync()
    {
        await InvokeAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the styles of {{style}}.
            Always state the requested style of the poem.
            """,
            HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            new HandlebarsPromptTemplateFactory());
    }

    [Fact]
    public async Task InvokeAgentWithLiquidTemplateAsync()
    {
        await InvokeAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the styles of {{style}}.
            Always state the requested style of the poem.
            """,
            LiquidPromptTemplateFactory.LiquidTemplateFormat,
            new LiquidPromptTemplateFactory());
    }

    private async Task InvokeAgentWithTemplateAsync(
        string instructionTemplate,
        string templateFormat,
        IPromptTemplateFactory templateFactory)
    {
        PromptTemplateConfig config = new()
        {
            Template = instructionTemplate,
            TemplateFormat = templateFormat,
        };

        // Define the Prompt Agent
        ProjectsAgentVersion promptAgent = await this.CreatePromptAgentAsync("Poet", new DeclarativeAgentDefinition(DeploymentName));

        // Create the agent
        ChatCompletionAgent agent =
            new(config, templateFactory)
            {
                Kernel = this.CreateKernel(promptAgent),
                Arguments = new()
                {
                    {"style", "haiku"}
                },
            };

        await InvokeAgentWithTemplateAsync(agent, promptAgent);
    }

    private async Task InvokeAgentWithTemplateAsync(ChatCompletionAgent agent, ProjectsAgentVersion promptAgent)
    {
        // Create a thread for the agent conversation.
        ChatHistoryAgentThread thread = new();

        try
        {
            // Respond to user input
            foreach ((string input, string? style) in s_inputs)
            {
                ChatMessageContent request = new(AuthorRole.User, input);
                this.WriteAgentChatMessage(request);

                KernelArguments? arguments = null;

                if (!string.IsNullOrWhiteSpace(style))
                {
                    arguments = new() { { "style", style } };
                }

                await foreach (ChatMessageContent message in agent.InvokeAsync(request, thread, options: new() { KernelArguments = arguments }))
                {
                    this.WriteAgentChatMessage(message);
                }
            }
        }
        finally
        {
            await thread.DeleteAsync();
            await this.DeletePromptAgentAsync(promptAgent);
        }
    }
}
