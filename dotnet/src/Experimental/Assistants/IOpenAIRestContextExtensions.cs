// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Context for interacting with OpenAI REST API.
/// </summary>
public static class IOpenAIRestContextExtensions
{
    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <returns>An <see cref="IAssistantBuilder"> for definition.</see></returns>
    public static IAssistantBuilder CreateAssistant(this IOpenAIRestContext restContext)
    {
        return new AssistantBuilder(restContext);
    }

    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="model">The LLM name</param>
    /// <param name="configurationPath">Path to a configuration file.</param>
    /// <param name="functions">Functions to associate with the tool.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The requested <see cref="IAssistant">.</see></returns>
    public static async Task<IAssistant> CreateAssistantAsync(
        this IOpenAIRestContext restContext,
        string model,
        string configurationPath,
        IEnumerable<ISKFunction>? functions = null,
        CancellationToken cancellationToken = default)
    {
        var yamlContent = File.ReadAllText(configurationPath);

        var deserializer = new DeserializerBuilder()
            //.WithTypeConverter(new ExecutionSettingsModelConverter()) // TODO: @chris MATTHEW
            .Build();

        var assistantKernelModel = deserializer.Deserialize<AssistantConfigurationModel>(yamlContent);

        return
            await new AssistantBuilder(restContext)
                .WithModel(model)
                .WithInstructions(assistantKernelModel.Instructions.Trim())
                .WithName(assistantKernelModel.Name.Trim())
                .WithDescription(assistantKernelModel.Description.Trim())
                .WithTools(functions ?? Array.Empty<ISKFunction>())
                .BuildAsync(cancellationToken)
                .ConfigureAwait(false);
    }

    /// <summary>
    /// Create a new assistant.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="model">The assistant chat model (required)</param>
    /// <param name="instructions">The assistant instructions (required)</param> // TODO: Why is this required???
    /// <param name="name">The assistant name (optional)</param>
    /// <param name="description">The assistant description(optional)</param>
    /// <returns>The requested <see cref="IAssistant">.</see></returns>
    public static async Task<IAssistant> CreateAssistantAsync(
        this IOpenAIRestContext restContext,
        string model,
        string instructions,
        string? name = null,
        string? description = null)
    {
        return
            await new AssistantBuilder(restContext)
                .WithModel(model)
                .WithInstructions(instructions)
                .WithName(name)
                .WithDescription(description)
                .BuildAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieve an existing assistant, by identifier.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">The assistant identifier</param>
    /// <param name="functions">Functions to initialize as assistant tools</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="IAssistant"> instance.</see></returns>
    public static Task<IAssistant> GetAssistantAsync(this IOpenAIRestContext restContext, string assistantId, IEnumerable<ISKFunction>? functions = null, CancellationToken cancellationToken = default)
    {
        return Assistant.GetAsync(restContext, assistantId, functions, cancellationToken);
    }

    /// <summary>
    /// Modify an existing assistant
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantToModify">Instance ID of assistant to modify</param>
    /// <param name="model">New model, if not null</param>
    /// <param name="instructions">New instructions, if not null</param>
    /// <param name="name">New name, if not null</param>
    /// <param name="description">New description, if not null</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>Modified <see cref="IAssistant"> instance.</see></returns>
    public static Task<IAssistant> ModifyAssistantAsync(
        this IOpenAIRestContext restContext,
        string assistantToModify,
        string? model = null,
        string? instructions = null,
        string? name = null,
        string? description = null,
        CancellationToken cancellationToken = default)
    {
        return Assistant.ModifyAsync(restContext, assistantToModify, model, instructions, name, description, cancellationToken);
    }

    /// <summary>
    /// Delete an existing assistant
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="assistantId">Instance ID of assistant to delete</param>
    /// <param name="cancellationToken">A cancellation token</param>
    public static Task DeleteAssistantAsync(
        this IOpenAIRestContext restContext,
        string assistantId,
        CancellationToken cancellationToken = default)
    {
        return Assistant.DeleteAsync(restContext, assistantId, cancellationToken);
    }

    /// <summary>
    /// List existing Assistant instances from OpenAI
    /// </summary>
    /// <param name="restContext">Context to make calls to OpenAI</param>
    /// <param name="limit">A limit on the number of objects to be returned.
    /// Limit can range between 1 and 100, and the default is 20.</param>
    /// <param name="ascending">Set to true to sort by ascending created_at timestamp
    /// instead of descending.</param>
    /// <param name="after">A cursor for use in pagination. This is an object ID that defines
    /// your place in the list. For instance, if you make a list request and receive 100 objects,
    /// ending with obj_foo, your subsequent call can include after=obj_foo in order to
    /// fetch the next page of the list.</param>
    /// <param name="before">A cursor for use in pagination. This is an object ID that defines
    /// your place in the list. For instance, if you make a list request and receive 100 objects,
    /// ending with obj_foo, your subsequent call can include before=obj_foo in order to
    /// fetch the previous page of the list.</param>
    /// <returns>List of retrieved Assistants</returns>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An enumeration of assistant definitions</returns>
    public static Task<IList<IAssistant>> ListAssistantsAsync(
        this IOpenAIRestContext restContext,
        int limit = 20,
        bool ascending = false,
        string? after = null,
        string? before = null,
        CancellationToken cancellationToken = default)
    {
        return Assistant.ListAsync(restContext, limit, ascending, after, before, cancellationToken);
    }

    /// <summary>
    /// Create a new thread.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="IChatThread"> instance.</see></returns>
    public static Task<IChatThread> CreateThreadAsync(this IOpenAIRestContext restContext, CancellationToken cancellationToken = default)
    {
        return ChatThread.CreateAsync(restContext, cancellationToken);
    }

    /// <summary>
    /// Retrieve an existing thread.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="threadId">The thread identifier</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="IChatThread"> instance.</see></returns>
    public static Task<IChatThread> GetThreadAsync(this IOpenAIRestContext restContext, string threadId, CancellationToken cancellationToken = default)
    {
        return ChatThread.GetAsync(restContext, threadId, cancellationToken);
    }

    /// <summary>
    /// Delete a thread.
    /// </summary>
    /// <param name="restContext">A context for accessing OpenAI REST endpoint</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="IChatThread"> instance.</see></returns>
    public static Task<IChatThread> DeleteThreadAsync(this IOpenAIRestContext restContext, CancellationToken cancellationToken = default)
    {
        return ChatThread.CreateAsync(restContext, cancellationToken);
    }
}
