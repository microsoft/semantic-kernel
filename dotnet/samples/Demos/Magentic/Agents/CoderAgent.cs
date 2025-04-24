// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.Assistants;

namespace Magentic.Agents;

/// <summary>
/// The definition and factory for the Writer agent.
/// </summary>
public static class CoderAgent
{
    /// <summary>
    /// The agent description.
    /// </summary>
    public const string Description =
        """
        A helpful assistant that is able to write and execute code in order to solve problems.
        """;

    /// <summary>
    /// The agent instructions.
    /// </summary>
    public const string Instructions =
        """
        Solve the problem in response to the most recent direction.
        When you are unsure, you may ask for clarification.
        When feedback has been provided for a solution you shared in a prior response, update your solution based on that feedback.
        """;

    /// <summary>
    /// Creates a new agent.
    /// </summary>
    /// <param name="kernel">A kernel with the required services for the agent</param>
    public static async Task<OpenAIAssistantAgent> CreateAsync(Kernel kernel)
    {
        AssistantClient client = kernel.GetRequiredService<AssistantClient>();
        string model = kernel.GetRequiredService<string>();
        Assistant assistant =
            await client.CreateAssistantAsync(
                model,
                nameof(CoderAgent),
                Description,
                Instructions,
                enableCodeInterpreter: true).ConfigureAwait(false);

        return new OpenAIAssistantAgent(assistant, client);
    }
}
