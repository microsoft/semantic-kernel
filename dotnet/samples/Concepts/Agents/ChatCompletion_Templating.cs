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
    private static readonly (string Input, string? Style)[] s_inputs =
        [
            (Input: "Home cooking is great.", Style: null),
            (Input: "Talk about world peace.", Style: "iambic pentameter"),
            (Input: "Say something about doing your best.", Style: "e. e. cummings"),
            (Input: "What do you think about having fun?", Style: "old school rap")
        ];

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task InvokeAgentWithInstructionsTemplate(bool useChatClient)
    {
        // Instruction based template always processed by KernelPromptTemplateFactory
        ChatCompletionAgent agent =
            new()
            {
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient),
                Instructions =
                    """
                    Write a one verse poem on the requested topic in the style of {{$style}}.
                    Always state the requested style of the poem.
                    """,
                Arguments = new KernelArguments()
                {
                    {"style", "haiku"}
                }
            };

        await InvokeChatCompletionAgentWithTemplateAsync(agent);

        chatClient?.Dispose();
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task InvokeAgentWithKernelTemplate(bool useChatClient)
    {
        // Default factory is KernelPromptTemplateFactory
        await InvokeChatCompletionAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the style of {{$style}}.
            Always state the requested style of the poem.
            """,
            PromptTemplateConfig.SemanticKernelTemplateFormat,
            new KernelPromptTemplateFactory(),
            useChatClient);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task InvokeAgentWithHandlebarsTemplate(bool useChatClient)
    {
        await InvokeChatCompletionAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the style of {{style}}.
            Always state the requested style of the poem.
            """,
            HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            new HandlebarsPromptTemplateFactory(),
            useChatClient);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task InvokeAgentWithLiquidTemplate(bool useChatClient)
    {
        await InvokeChatCompletionAgentWithTemplateAsync(
            """
            Write a one verse poem on the requested topic in the style of {{style}}.
            Always state the requested style of the poem.
            """,
            LiquidPromptTemplateFactory.LiquidTemplateFormat,
            new LiquidPromptTemplateFactory(),
            useChatClient);
    }

    private async Task InvokeChatCompletionAgentWithTemplateAsync(
        string instructionTemplate,
        string templateFormat,
        IPromptTemplateFactory templateFactory,
        bool useChatClient)
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
                Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient),
                Arguments = new KernelArguments()
                {
                    {"style", "haiku"}
                }
            };

        await InvokeChatCompletionAgentWithTemplateAsync(agent);

        chatClient?.Dispose();
    }

    private async Task InvokeChatCompletionAgentWithTemplateAsync(ChatCompletionAgent agent)
    {
        ChatHistory chat = [];

        foreach ((string input, string? style) in s_inputs)
        {
            // Add input to chat
            ChatMessageContent request = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(request);

            KernelArguments? arguments = null;

            if (!string.IsNullOrWhiteSpace(style))
            {
                // Override style template parameter
                arguments = new() { { "style", style } };
            }

            // Process agent response
            await foreach (ChatMessageContent message in agent.InvokeAsync(request, options: new() { KernelArguments = arguments }))
            {
                chat.Add(message);
                this.WriteAgentChatMessage(message);
            }
        }
    }
}
