// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;

namespace Agents;

/// <summary>
/// Demonstrate parameterized template instruction for <see cref="ChatCompletionAgent"/>.
/// </summary>
public class ChatCompletion_Templating(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private readonly static (string Input, string? Style)[] s_inputs =
        [
            (Input: "Home cooking is the great.", Style: null),
            (Input: "Talk about world peace.", Style: "iambic pentameter"),
            (Input: "Say something about doing your best.", Style: "e. e. cummings"),
            (Input: "What do you think about having fun?", Style: "old school rap")
        ];

    [Fact]
    public async Task InvokeAgentWithKernelTemplateAsync()
    {
        // Default factory is KernelPromptTemplateFactory
        await InvokeChatCompletionAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the style of {{$style}}.
            Always state the requested style of the poem.
            """);
    }

    [Fact]
    public async Task InvokeAgentWithHandlebarsTemplateAsync()
    {
        await InvokeChatCompletionAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the style of {{style}}.
            Always state the requested style of the poem.
            """,
            HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            new HandlebarsPromptTemplateFactory());
    }

    [Fact]
    public async Task InvokeAgentWithLiquidTemplateAsync()
    {
        await InvokeChatCompletionAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the style of {{style}}.
            Always state the requested style of the poem.
            """,
            LiquidPromptTemplateFactory.LiquidTemplateFormat,
            new LiquidPromptTemplateFactory());
    }

    private async Task InvokeChatCompletionAgentWithTemplateAsync(
        string instructionTemplate,
        string? templateFormat = null,
        IPromptTemplateFactory? templateFactory = null)
    {
        // Define the agent
        PromptTemplateConfig templateConfig =
            new()
            {
                Template = instructionTemplate,
                TemplateFormat = templateFormat,
            };
        ChatCompletionAgent agent =
            new(templateConfig, templateFactory)
            {
                Kernel = this.CreateKernelWithChatCompletion(),
                Arguments = new KernelArguments()
                {
                    {"style", "haiku"}
                }
            };

        ChatHistory chat = [];

        // Respond to user input
        foreach ((string input, string? style) in s_inputs)
        {
            ChatMessageContent request = new(AuthorRole.User, input);
            chat.Add(request);
            this.WriteAgentChatMessage(request);

            KernelArguments? arguments = null;

            if (!string.IsNullOrWhiteSpace(style))
            {
                arguments = new() { { "style", style } };
            }

            await foreach (ChatMessageContent message in agent.InvokeAsync(chat, arguments))
            {
                chat.Add(message);
                this.WriteAgentChatMessage(message);
            }
        }
    }
}
