// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace Magentic.Agents;

/// <summary>
/// The definition and factory for the Writer agent.
/// </summary>
public static class ResearchAgent
{
    /// <summary>
    /// The agent description.
    /// </summary>
    public const string Description =
        """
        A helpful assistant that is able to search the Internet to provide information in response to a request.
        """;

    /// <summary>
    /// The agent instructions.
    /// </summary>
    public const string Instructions =
        """
        Respond by providing information in response to the most recent direction without imposing any assumptions.
        Request clarification for any ambiguity.
        When feedback has been provided for information you shared in a prior response, focus on addressing the feedback.
        """;

    /// <summary>
    /// Creates a new agent.
    /// </summary>
    /// <param name="kernel">A kernel with the required services for the agent</param>
    /// <param name="serviceId">An optional service identifier to resolve the chat-completion service</param>
    public static ChatCompletionAgent Create(Kernel kernel, string? serviceId = null)
    {
        return
            new ChatCompletionAgent()
            {
                Name = nameof(ResearchAgent),
                Instructions = Instructions,
                Description = Description,
                Kernel = kernel,
                Arguments = new KernelArguments(new PromptExecutionSettings() { ServiceId = serviceId })
            };
    }
}
