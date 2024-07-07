// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines an assistant.
/// </summary>
public sealed class OpenAIAssistantDefinition
{
    /// <summary>
    /// Identifies the AI model targeted by the agent.
    /// </summary>
    public string? ModelName { get; init; }

    /// <summary>
    /// The description of the assistant.
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// The assistant's unique id.  (Ignored on create.)
    /// </summary>
    public string? Id { get; init; }

    /// <summary>
    /// The system instructions for the assistant to use.
    /// </summary>
    public string? Instructions { get; init; }

    /// <summary>
    /// The name of the assistant.
    /// </summary>
    public string? Name { get; init; }

    /// <summary>
    /// Optional file-ids made available to the code_interpreter tool.
    /// </summary>
    public IReadOnlyList<string>? CodeInterpterFileIds { get; init; }

    /// <summary>
    /// Set if code-interpreter is enabled.
    /// </summary>
    public bool EnableCodeInterpreter { get; init; }

    /// <summary>
    /// Set if json response-format is enabled.
    /// </summary>
    public bool EnableJsonResponse { get; init; }

    /// <summary>
    /// A set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.Keys
    /// may be up to 64 characters in length and values may be up to 512 characters in length.
    /// </summary>
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }

    /// <summary>
    /// The sampling temperature to use, between 0 and 2.
    /// </summary>
    public float? Temperature { get; init; }

    /// <summary>
    /// An alternative to sampling with temperature, called nucleus sampling, where the model
    /// considers the results of the tokens with top_p probability mass.
    /// So 0.1 means only the tokens comprising the top 10% probability mass are considered.
    /// </summary>
    /// <remarks>
    /// Recommended to set this or temperature but not both.
    /// </remarks>
    public float? TopP { get; init; }

    /// <summary>
    /// Enables file-serach if specified.
    /// </summary>
    public string? VectorStoreId { get; init; }

    /// <summary>
    /// Default execution settings for each agent invocation.
    /// </summary>
    public OpenAIAssistantExecutionSettings? ExecutionSettings { get; init; }
}
