// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines an assistant.
/// </summary>
public sealed class OpenAIAssistantDefinition : OpenAIAssistantCapabilities
{
    /// <summary>
    /// Identifies the AI model targeted by the agent.
    /// </summary>
    public string ModelId { get; }

    /// <summary>
    /// The description of the assistant.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Description { get; init; }

    /// <summary>
    /// The assistant's unique id.  (Ignored on create.)
    /// </summary>
    public string Id { get; init; } = string.Empty;

    /// <summary>
    /// The system instructions for the assistant to use.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Instructions { get; init; }

    /// <summary>
    /// The name of the assistant.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Name { get; init; }

    /// <summary>
    /// Provide the captured template format for the assistant if needed for agent retrieval.
    /// (<see cref="OpenAIAssistantAgent.RetrieveAsync"/>)
    /// </summary>
    [JsonIgnore]
    public string? TemplateFactoryFormat
    {
        get
        {
            if (this.Metadata == null)
            {
                return null;
            }

            this.Metadata.TryGetValue(OpenAIAssistantAgent.TemplateMetadataKey, out string? templateFormat);

            return templateFormat;
        }
    }
    /// Optional file-ids made available to the code_interpreter tool, if enabled.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IReadOnlyList<string>? CodeInterpreterFileIds { get; init; }

    /// <summary>
    /// Set if code-interpreter is enabled.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool EnableCodeInterpreter { get; init; }

    /// <summary>
    /// Set if file-search is enabled.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool EnableFileSearch { get; init; }

    /// <summary>
    /// Set if json response-format is enabled.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool EnableJsonResponse { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantDefinition"/> class.
    /// </summary>
    /// <param name="modelId">The targeted model</param>
    [JsonConstructor]
    public OpenAIAssistantDefinition(string modelId)
        : base(modelId) { }
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }

    /// <summary>
    /// The sampling temperature to use, between 0 and 2.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? Temperature { get; init; }
    /// Provide the captured template format for the assistant if needed for agent retrieval.
    /// (<see cref="OpenAIAssistantAgent.RetrieveAsync"/>)
    /// </summary>
    [JsonIgnore]
    public string? TemplateFactoryFormat
    {
        get
        {
            if (this.Metadata == null)
            {
                return null;
            }

            this.Metadata.TryGetValue(OpenAIAssistantAgent.TemplateMetadataKey, out string? templateFormat);

            return templateFormat;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantDefinition"/> class.
    /// </summary>
    /// <param name="modelId">The targeted model</param>
    [JsonConstructor]
    public OpenAIAssistantDefinition(string modelId)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this.ModelId = modelId;
    }
        : base(modelId) { }
}
