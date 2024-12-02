// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Plugins.Manifest;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for loading and managing declarative agents and their Copilot Agent Plugins.
/// </summary>
public static class DeclarativeAgentExtensions
{
    /// <summary>
    /// Creates a chat completion agent from a declarative agent manifest asynchronously.
    /// </summary>
    /// <typeparam name="T">The type of the agent to create.</typeparam>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="filePath">The file path of the declarative agent manifest.</param>
    /// <param name="pluginParameters">Optional parameters for the Copilot Agent Plugin setup.</param>
    /// <param name="promptExecutionSettings">Optional prompt execution settings. Ensure you enable function calling.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created chat completion agent.</returns>
    public static async Task<T> CreateChatCompletionAgentFromDeclarativeAgentManifestAsync<T>(
        this Kernel kernel,
        string filePath,
        CopilotAgentPluginParameters? pluginParameters = null,
        PromptExecutionSettings? promptExecutionSettings = default,
        CancellationToken cancellationToken = default)
        where T : KernelAgent, new()
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(filePath);

        var loggerFactory = kernel.LoggerFactory;
        var logger = loggerFactory.CreateLogger(typeof(DeclarativeAgentExtensions)) ?? NullLogger.Instance;
        using var declarativeAgentFileJsonContents = DocumentLoader.LoadDocumentFromFilePathAsStream(filePath,
            logger);

        var results = await DCManifestDocument.LoadAsync(declarativeAgentFileJsonContents, new ReaderOptions
        {
            ValidationRules = [] // Disable validation rules
        }).ConfigureAwait(false);

        if (!results.IsValid)
        {
            var messages = results.Problems.Select(static p => p.Message).Aggregate(static (a, b) => $"{a}, {b}");
            throw new InvalidOperationException($"Error loading the manifest: {messages}");
        }

        var document = results.Document ?? throw new InvalidOperationException("Error loading the manifest");
        document.Instructions = await GetEffectiveInstructionsAsync(document.Instructions, logger, cancellationToken).ConfigureAwait(false);

        var agent = new T
        {
            Name = document.Name,
            Instructions = document.Instructions,
            Kernel = kernel,
            Arguments = new KernelArguments(promptExecutionSettings ?? new PromptExecutionSettings()
            {
                FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
            }),
            Description = document.Description,
            LoggerFactory = loggerFactory,
            Id = string.IsNullOrEmpty(document.Id) ? Guid.NewGuid().ToString() : document.Id,
        };

        await Task.WhenAll(document.Actions.Select(action => kernel.ImportPluginFromCopilotAgentPluginAsync(action.Id, action.File, pluginParameters, cancellationToken))).ConfigureAwait(false);
        return agent;
    }
    private static async Task<string?> GetEffectiveInstructionsAsync(string? source, ILogger logger, CancellationToken cancellationToken)
    {
        if (string.IsNullOrEmpty(source) ||
            !source.StartsWith("[$file('", StringComparison.OrdinalIgnoreCase) ||
            !source.EndsWith("')]", StringComparison.OrdinalIgnoreCase))
        {
            return source;
        }
#if NETCOREAPP3_0_OR_GREATER
        var filePath = source[8..^3];
#else
        var filePath = source.Substring(8, source.Length - 11);
#endif
        return await DocumentLoader.LoadDocumentFromFilePathAsync(filePath, logger, cancellationToken).ConfigureAwait(false);
    }
}
