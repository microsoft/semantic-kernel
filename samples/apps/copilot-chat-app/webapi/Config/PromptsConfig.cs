// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// Prompt configuration.
/// </summary>
public class PromptsConfig
{
    /// <summary>
    /// Token limit of the chat model.
    /// </summary>
    /// <remarks>https://platform.openai.com/docs/models/overview for token limits.</remarks>
    public int CompletionTokenLimit { get; set; }

    /// <summary>
    /// The token count left for the model to generate text after the prompt.
    /// </summary>
    public int ResponseTokenLimit { get; set; }

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
        if (this.CompletionTokenLimit <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(this.CompletionTokenLimit), $"{nameof(this.CompletionTokenLimit)} is not valid: '{this.CompletionTokenLimit}' is not greater than 0.");
        }

        if (this.ResponseTokenLimit <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(this.ResponseTokenLimit), $"{nameof(this.ResponseTokenLimit)} is not valid: '{this.ResponseTokenLimit}' is not greater than 0.");
        }

        if (this.ResponseTokenLimit > this.CompletionTokenLimit)
        {
            throw new ArgumentOutOfRangeException(nameof(this.ResponseTokenLimit), $"{nameof(this.ResponseTokenLimit)} is not valid: '{this.ResponseTokenLimit}' is greater than '{this.CompletionTokenLimit}'.");
        }

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
