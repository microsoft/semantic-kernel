// Copyright (c) Microsoft. All rights reserved.

using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Prompts;

/// <summary>
/// Represents the prompt registry that contains the prompt definitions and provides the handlers for the prompt `List` and `Get` requests.
/// </summary>
internal static class PromptRegistry
{
    private static readonly Dictionary<string, PromptDefinition> s_definitions = new();

    /// <summary>
    /// Registers a prompt definition.
    /// </summary>
    /// <param name="definition">The prompt definition to register.</param>
    public static void RegisterPrompt(PromptDefinition definition)
    {
        if (s_definitions.ContainsKey(definition.Prompt.Name))
        {
            throw new ArgumentException($"A prompt with the name '{definition.Prompt.Name}' is already registered.");
        }

        s_definitions[definition.Prompt.Name] = definition;
    }

    /// <summary>
    /// Handles the `Get` prompt requests.
    /// </summary>
    /// <param name="context">The request context.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the `Get` prompt request.</returns>
    public static async Task<GetPromptResult> HandlerGetPromptRequestsAsync(RequestContext<GetPromptRequestParams> context, CancellationToken cancellationToken)
    {
        // Make sure the prompt name is provided
        if (context.Params?.Name is not string { } promptName || string.IsNullOrEmpty(promptName))
        {
            throw new ArgumentException("Prompt name is required.");
        }

        // Look up the prompt handler
        if (!s_definitions.TryGetValue(promptName, out PromptDefinition? definition))
        {
            throw new ArgumentException($"No handler found for the prompt '{promptName}'.");
        }

        // Invoke the handler
        return await definition.Handler(context, cancellationToken);
    }

    /// <summary>
    /// Handles the `List` prompt requests.
    /// </summary>
    /// <param name="context">Context of the request.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the `List` prompt request.</returns>
    public static Task<ListPromptsResult> HandlerListPromptRequestsAsync(RequestContext<ListPromptsRequestParams> context, CancellationToken cancellationToken)
    {
        return Task.FromResult(new ListPromptsResult
        {
            Prompts = [.. s_definitions.Values.Select(d => d.Prompt)]
        });
    }
}
