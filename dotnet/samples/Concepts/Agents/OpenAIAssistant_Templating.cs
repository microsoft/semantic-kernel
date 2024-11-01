// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;

namespace Agents;

/// <summary>
/// Demonstrate parameterized template instruction  for <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public class OpenAIAssistant_Templating(ITestOutputHelper output) : BaseAgentsTest(output)
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
        // Instruction based template always proceseed by KernelPromptTemplateFactory
        OpenAIAssistantAgent agent = await OpenAIAssistantAgent.CreateAsync(
                clientProvider: this.GetClientProvider(),
                definition: new OpenAIAssistantDefinition(this.Model)
                {
                    Instructions =
                        """
                        Write a one verse poem on the requested topic in the styles of {{$style}}.
                        Always state the requested style of the poem.
                        """,
                    Metadata = AssistantSampleMetadata
                },
                kernel: new Kernel(),
                defaultArguments: new KernelArguments()
                {
                    {"style", "haiku"}
                });

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
            """);
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
        string? templateFormat = null,
        IPromptTemplateFactory? templateFactory = null)
    {
        // Define the agent
        OpenAIAssistantAgent agent = await OpenAIAssistantAgent.CreateFromTemplateAsync(
                clientProvider: this.GetClientProvider(),
                capabilities: new OpenAIAssistantCapabilities(this.Model)
                {
                    Metadata = AssistantSampleMetadata
                },
                kernel: new Kernel(),
                defaultArguments: new KernelArguments()
                {
                    {"style", "haiku"}
                },
                templateConfig: new PromptTemplateConfig
                {
                    Template = instructionTemplate,
                    TemplateFormat = templateFormat,
                },
                templateFactory);

        await InvokeAssistantAgentWithTemplateAsync(agent);
    }

    private async Task InvokeAssistantAgentWithTemplateAsync(OpenAIAssistantAgent agent)
    {
        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        try
        {
            // Respond to user input
            foreach ((string input, string? style) in s_inputs)
            {
                ChatMessageContent request = new(AuthorRole.User, input);
                await agent.AddChatMessageAsync(threadId, request);
                this.WriteAgentChatMessage(request);

                KernelArguments? arguments = null;

                if (!string.IsNullOrWhiteSpace(style))
                {
                    arguments = new() { { "style", style } };
                }

                await foreach (ChatMessageContent message in agent.InvokeAsync(threadId, arguments))
                {
                    this.WriteAgentChatMessage(message);
                }
            }
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }
    }
}
