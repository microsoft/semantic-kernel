// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// Prompt configuration.
/// </summary>
public class PromptsConfig
{
    // System
    public string KnowledgeCutoffDate { get; set; } = string.Empty;
    public string InitialBotMessage { get; set; } = string.Empty;
    public string SystemDescription { get; set; } = string.Empty;
    public string SystemResponse { get; set; } = string.Empty;

    // Intent extraction
    public string SystemIntent { get; set; } = string.Empty;
    public string SystemIntentContinuation { get; set; } = string.Empty;

    // Memory extraction
    public string SystemCognitive { get; set; } = string.Empty;
    public string MemoryFormat { get; set; } = string.Empty;
    public string MemoryAntiHallucination { get; set; } = string.Empty;
    public string MemoryContinuation { get; set; } = string.Empty;

    // Long-term memory
    public string LongTermMemoryName { get; set; } = string.Empty;
    public string LongTermMemoryExtraction { get; set; } = string.Empty;

    // Working memory
    public string WorkingMemoryName { get; set; } = string.Empty;
    public string WorkingMemoryExtraction { get; set; } = string.Empty;

    public void Validate()
    {
        Validate(this.KnowledgeCutoffDate, nameof(this.KnowledgeCutoffDate));
        Validate(this.InitialBotMessage, nameof(this.InitialBotMessage));
        Validate(this.SystemDescription, nameof(this.SystemDescription));
        Validate(this.SystemResponse, nameof(this.SystemResponse));
        Validate(this.SystemIntent, nameof(this.SystemIntent));
        Validate(this.SystemIntentContinuation, nameof(this.SystemIntentContinuation));
        Validate(this.SystemCognitive, nameof(this.SystemCognitive));
        Validate(this.MemoryFormat, nameof(this.MemoryFormat));
        Validate(this.MemoryAntiHallucination, nameof(this.MemoryAntiHallucination));
        Validate(this.MemoryContinuation, nameof(this.MemoryContinuation));
        Validate(this.LongTermMemoryName, nameof(this.LongTermMemoryName));
        Validate(this.LongTermMemoryExtraction, nameof(this.LongTermMemoryExtraction));
        Validate(this.WorkingMemoryName, nameof(this.WorkingMemoryName));
        Validate(this.WorkingMemoryExtraction, nameof(this.WorkingMemoryExtraction));
    }

    private static void Validate(string property, string propertyName)
    {
        if (string.IsNullOrWhiteSpace(property))
        {
            throw new ArgumentException(propertyName, $"{propertyName} is not valid: '{property}'.");
        }
    }
}
