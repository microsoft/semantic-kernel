// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines the capabilities of an assistant.
/// </summary>
[Experimental("SKEXP0110")]
[Obsolete("Use the OpenAI.Assistants.AssistantClient.CreateAssistantAsync() to create an assistant definition.")]
public class OpenAIAssistantCapabilities
{
    /// <summary>
    /// Gets the AI model targeted by the agent.
    /// </summary>
    public string ModelId { get; }

    /// <summary>
    /// Gets the assistant's unique ID. (Ignored on create.)
    /// </summary>
    public string Id { get; init; } = string.Empty;

    /// <summary>
    /// Gets optional file IDs made available to the code-interpreter tool, if enabled.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IReadOnlyList<string>? CodeInterpreterFileIds { get; init; }

    /// <summary>
    /// Gets a value that indicates whether the code-interpreter tool is enabled.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool EnableCodeInterpreter { get; init; }

    /// <summary>
    /// Gets a value that indicates whether the file_search tool is enabled.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool EnableFileSearch { get; init; }

    /// <summary>
    /// Gets a value that indicates whether the JSON response format is enabled.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool EnableJsonResponse { get; init; }

    /// <summary>
    /// Gets a set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.
    /// </summary>
    /// <remarks>
    /// Keys can be up to 64 characters in length, and values can be up to 512 characters in length.
    /// </remarks>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }

    /// <summary>
    /// Gets the sampling temperature to use, between 0 and 2.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? Temperature { get; init; }

    /// <summary>
    /// Gets the probability mass of tokens whose results are considered in nucleus sampling.
    /// </summary>
    /// <remarks>
    /// It's recommended to set this property or <see cref="Temperature"/>, but not both.
    ///
    /// Nucleus sampling is an alternative to sampling with temperature where the model
    /// considers the results of the tokens with <see cref="TopP"/> probability mass.
    /// For example, 0.1 means only the tokens comprising the top 10% probability mass are considered.
    /// </remarks>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? TopP { get; init; }

    /// <summary>
    /// Gets the vector store ID. Requires file-search if specified.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? VectorStoreId { get; init; }

    /// <summary>
    /// Gets the default execution options for each agent invocation.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public OpenAIAssistantExecutionOptions? ExecutionOptions { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantDefinition"/> class.
    /// </summary>
    /// <param name="modelId">The targeted model.</param>
    [JsonConstructor]
    public OpenAIAssistantCapabilities(string modelId)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this.ModelId = modelId;
    }
}
