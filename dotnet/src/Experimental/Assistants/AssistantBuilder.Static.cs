// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Context for interacting with OpenAI REST API.
/// </summary>
public partial class AssistantBuilder
{
    /// <summary>
    /// Create a new assistant from a yaml formatted string.
    /// </summary>
    /// <param name="apiKey">The OpenAI API key</param>
    /// <param name="model">The LLM name</param>
    /// <param name="template">YAML assistant definition.</param>
    /// <param name="plugins">Plugins to associate with the tool.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The requested <see cref="IAssistant">.</see></returns>
    public static async Task<IAssistant> FromDefinitionAsync(
        string apiKey,
        string model,
        string template,
        ISKPluginCollection? plugins = null,
        CancellationToken cancellationToken = default)
    {
        var deserializer = new DeserializerBuilder().Build();

        var assistantKernelModel = deserializer.Deserialize<AssistantConfigurationModel>(template);

        return
            await new AssistantBuilder()
                .WithOpenAIChatCompletionService(model, apiKey)
                .WithInstructions(assistantKernelModel.Instructions.Trim())
                .WithName(assistantKernelModel.Name.Trim())
                .WithDescription(assistantKernelModel.Description.Trim())
                .WithPlugins(plugins ?? new SKPluginCollection())
                .BuildAsync(cancellationToken)
                .ConfigureAwait(false);
    }

    /// <summary>
    /// Create a new assistant from a yaml template.
    /// </summary>
    /// <param name="apiKey">The OpenAI API key</param>
    /// <param name="model">The LLM name</param>
    /// <param name="definitionPath">Path to a configuration file.</param>
    /// <param name="plugins">Plugins to associate with the tool.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The requested <see cref="IAssistant">.</see></returns>
    public static Task<IAssistant> FromTemplateAsync(
        string apiKey,
        string model,
        string definitionPath,
        ISKPluginCollection? plugins = null,
        CancellationToken cancellationToken = default)
    {
        var yamlContent = File.ReadAllText(definitionPath);

        return FromDefinitionAsync(apiKey, model, yamlContent, plugins, cancellationToken);
    }

    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="apiKey">The OpenAI API key</param>
    /// <param name="model">The assistant chat model (required)</param>
    /// <param name="instructions">The assistant instructions (required)</param>
    /// <param name="name">The assistant name (optional)</param>
    /// <param name="description">The assistant description(optional)</param>
    /// <returns>The requested <see cref="IAssistant">.</see></returns>
    public static async Task<IAssistant> NewAsync(
        string apiKey,
        string model,
        string instructions,
        string? name = null,
        string? description = null)
    {
        return
            await new AssistantBuilder()
                .WithOpenAIChatCompletionService(model, apiKey)
                .WithInstructions(instructions)
                .WithName(name)
                .WithDescription(description)
                .BuildAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieve an existing assistant, by identifier.
    /// </summary>
    /// <param name="apiKey">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="plugins">Plugins to initialize as assistant tools</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Assistant"> instance.</see></returns>
    public static async Task<IAssistant> GetAssistantAsync(
        string apiKey,
        string assistantId,
        ISKPluginCollection? plugins = null,
        CancellationToken cancellationToken = default)
    {
        var restContext = new OpenAIRestContext(apiKey);
        var resultModel =
            await restContext.GetAssistantModelAsync(assistantId, cancellationToken).ConfigureAwait(false) ??
            throw new SKException($"Unexpected failure retrieving assistant: no result. ({assistantId})");
        var chatService = new OpenAIChatCompletion(resultModel.Model, apiKey);

        return new Assistant(resultModel, chatService, restContext, plugins);
    }
}
