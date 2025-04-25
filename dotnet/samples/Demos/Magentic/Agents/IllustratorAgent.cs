// Copyright (c) Microsoft. All rights reserved.

using Magentic.Agents.Internal;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace Magentic.Agents;

/// <summary>
/// The definition and factory for the Illustrator agent.
/// </summary>
public static class IllustratorAgent
{
    /// <summary>
    /// The agent description.
    /// </summary>
    public const string Description =
        """
        A helpful assistant that is able to produce images in response to a request.
        """;

    /// <summary>
    /// The agent instructions.
    /// </summary>
    public const string Instructions =
        """
        Respond by generating an image in response to the most recent direction.
        When you are unsure, you may ask for clarification.
        Make sure the images have consistent characters and style.
        Format a reference to the generated image as a markdown link your response.
        """;

    /// <summary>
    /// Creates a new agent.
    /// </summary>
    /// <param name="kernel">A kernel with the required services for the agent</param>
    /// <param name="serviceId">An optional service identifier to resolve the chat-completion service</param>
    public static ChatCompletionAgent Create(Kernel kernel, string? serviceId = null)
    {
        kernel.Plugins.AddFromType<IllustratorPlugin>(serviceProvider: kernel.Services);

        return
            new ChatCompletionAgent()
            {
                Name = nameof(IllustratorAgent),
                Instructions = Instructions,
                Description = Description,
                Kernel = kernel,
                Arguments =
                    new KernelArguments(
                        new PromptExecutionSettings()
                        {
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
                            ServiceId = serviceId,
                        }),
            };
    }
}
