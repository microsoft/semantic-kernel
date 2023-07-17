// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using SemanticKernel.Service.Options;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Configuration options for the chat
/// </summary>
public class PromptsOptions
{
    public const string PropertyName = "ReusablePromptVariables";

    /// <summary>
    /// Token limit of the chat model.
    /// </summary>
    /// <remarks>https://platform.openai.com/docs/models/overview for token limits.</remarks>
    [Required, Range(0, int.MaxValue)] public int CompletionTokenLimit { get; set; }

    /// <summary>
    /// Weight of memories in the contextual part of the final prompt.
    /// Contextual prompt excludes all the system commands and user intent.
    /// </summary>
    internal double MemoriesResponseContextWeight { get; } = 0.3;

    /// <summary>
    /// Weight of documents in the contextual part of the final prompt.
    /// Contextual prompt excludes all the system commands and user intent.
    /// </summary>
    internal double DocumentContextWeight { get; } = 0.3;

    /// <summary>
    /// Weight of information returned from planner (i.e., responses from OpenAPI skills).
    /// Contextual prompt excludes all the system commands and user intent.
    /// </summary>
    internal double ExternalInformationContextWeight { get; } = 0.3;

    /// <summary>
    /// Minimum relevance of a semantic memory to be included in the final prompt.
    /// The higher the value, the answer will be more relevant to the user intent.
    /// </summary>
    internal double SemanticMemoryMinRelevance { get; } = 0.8;

    /// <summary>
    /// Minimum relevance of a document memory to be included in the final prompt.
    /// The higher the value, the answer will be more relevant to the user intent.
    /// </summary>
    internal double DocumentMemoryMinRelevance { get; } = 0.8;

    // System
    [Required, NotEmptyOrWhitespace] public string KnowledgeCutoffDate { get; set; } = string.Empty;
    [Required, NotEmptyOrWhitespace] public string InitialBotMessage { get; set; } = string.Empty;

    // Memory extraction
    [Required, NotEmptyOrWhitespace] public string MemoryFormat { get; set; } = string.Empty;

    // Memory map
    internal List<string> MemoryTypes => new()
    {
        "LongTermMemory",
        "WorkingMemory"
    };
}
