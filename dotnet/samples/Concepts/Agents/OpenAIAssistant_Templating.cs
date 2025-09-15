// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;
using OpenAI.Assistants;

namespace Agents;

/// <summary>
/// Demonstrate parameterized template instruction  for <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public class OpenAIAssistant_Templating(ITestOutputHelper output) : BaseAssistantTest(output)
{
    private readonly static (string Input, string? Style)[] s_inputs =
        [
            (Input: "Home cooking is great.", Style: null),
            (Input: "Talk about world peace.", Style: "iambic pentameter"),
            (Input: "Say something about doing your best.", Style: "e. e. cummings"),
            (Input: "What do you think about having fun?", Style: "old school rap")
        ];

    [Fact]
    public async Task InvokeAgentWithInstructionsAsync()
    {
        // Define the assistant
        Assistant assistant =
            await this.AssistantClient.CreateAssistantAsync(
                this.Model,
                instructions:
                    """
                    Write a one verse poem on the requested topic in the styles of {{$style}}.
                    Always state the requested style of the poem.
                    """,
                metadata: SampleMetadata);

        // Create the agent
        OpenAIAssistantAgent agent = new(assistant, this.AssistantClient)
        {
            Arguments = new()
            {
                {"style", "haiku"}
            },
        };

        await InvokeAssistantAgentWithTemplateAsync(agent);
    }

    [Fact]
    public async Task InvokeAgentWithKernelTemplateAsync()
    {
        // Default factory is KernelPromptTemplateFactory
        await InvokeAssistantAgentWithTemplateAsync(
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
        await InvokeAssistantAgentWithTemplateAsync(
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
        await InvokeAssistantAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the styles of {{style}}.
            Always state the requested style of the poem.
            """,
            LiquidPromptTemplateFactory.LiquidTemplateFormat,
            new LiquidPromptTemplateFactory());
    }

    private async Task InvokeAssistantAgentWithTemplateAsync(
        string instructionTemplate,
        string templateFormat,
        IPromptTemplateFactory templateFactory)
    {
        PromptTemplateConfig config = new()
        {
            Template = instructionTemplate,
            TemplateFormat = templateFormat,
        };

        // Define the assistant
        Assistant assistant =
            await this.AssistantClient.CreateAssistantFromTemplateAsync(
                this.Model,
                config,
                metadata: SampleMetadata);

        // Create the agent
        OpenAIAssistantAgent agent = new(assistant, this.AssistantClient, plugins: null, templateFactory, templateFormat)
        {
            Arguments = new()
            {
                {"style", "haiku"}
            },
        };

        await InvokeAssistantAgentWithTemplateAsync(agent);
    }

    private async Task InvokeAssistantAgentWithTemplateAsync(OpenAIAssistantAgent agent)
    {
        // Create a thread for the agent conversation.
        OpenAIAssistantAgentThread thread = new(this.AssistantClient, metadata: SampleMetadata);

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
            await this.AssistantClient.DeleteAssistantAsync(agent.Id);
        }
    }
}
