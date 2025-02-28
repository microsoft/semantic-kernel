// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines an assistant.
/// </summary>
[Experimental("SKEXP0110")]
[Obsolete("Use the OpenAI.Assistants.AssistantClient.CreateAssistantAsync() to create an assistant definition.")]
public sealed class OpenAIAssistantDefinition : OpenAIAssistantCapabilities
{
    /// <summary>
    /// Gets the description of the assistant.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Description { get; init; }

    /// <summary>
    /// Gets the system instructions for the assistant to use.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Instructions { get; init; }

    /// <summary>
    /// Gets the name of the assistant.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Name { get; init; }

    /// <summary>
    /// Gets the captured template format for the assistant if needed for agent retrieval
    /// (<see cref="OpenAIAssistantAgent.RetrieveAsync"/>).
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
    /// <param name="modelId">The targeted model.</param>
    [JsonConstructor]
    public OpenAIAssistantDefinition(string modelId)
        : base(modelId) { }
}
