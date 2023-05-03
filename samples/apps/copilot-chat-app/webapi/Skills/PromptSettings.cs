// Copyright (c) Microsoft. All rights reserved.

using SemanticKernel.Service.Config;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// Settings for semantic function prompts.
/// </summary>
public class PromptSettings
{
    /// <summary>
    /// Values from the prompt configuration.
    /// </summary>
    private readonly PromptsConfig _promptsConfig;

    public PromptSettings(PromptsConfig promptsConfig)
    {
        this._promptsConfig = promptsConfig;
    }

    internal int ResponseTokenLimit { get; } = 1024;
    internal int CompletionTokenLimit { get; } = 8192;

    /// <summary>
    /// Weight of memories in the contextual part of the final prompt.
    /// Contextual prompt excludes all the system commands.
    /// </summary>
    internal double MemoriesResponseContextWeight { get; } = 0.3;

    /// <summary>
    /// Weight of documents in the contextual part of the final prompt.
    /// Contextual prompt excludes all the system commands.
    /// </summary>
    internal double DocumentContextWeight { get; } = 0.3;

    /// <summary>
    /// Weight of information returned from planner (i.e., responses from OpenAPI skills).
    /// Percentage calculated from remaining token limit after memories response and document context have already been allocated.
    /// Contextual prompt excludes all the system commands.
    /// </summary>
    internal double RelatedInformationContextWeight { get; } = 0.75;

    /// <summary>
    /// Maximum number of tokens per line that will be used to split a document into lines.
    /// Setting this to a low value will result in higher context granularity, but
    /// takes longer to process the entire document into embeddings.
    /// Default to 30 tokens as suggested by OpenAI:
    /// https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
    /// </summary>
    internal int DocumentLineSplitMaxTokens { get; } = 30;

    /// <summary>
    /// Maximum number of tokens per paragraph that will be used to combine lines into paragraphs.
    /// Setting this to a low value will result in higher context granularity, but
    /// takes longer to process the entire document into embeddings.
    /// Default to 100 tokens as suggested by OpenAI:
    /// https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them    /// </summary>
    internal int DocumentParagraphSplitMaxLines { get; } = 100;

    internal string KnowledgeCutoffDate => this._promptsConfig.KnowledgeCutoffDate;
    internal string InitialBotMessage => this._promptsConfig.InitialBotMessage;

    // System commands
    internal string SystemDescriptionPrompt => this._promptsConfig.SystemDescription;
    internal string SystemResponsePrompt => this._promptsConfig.SystemResponse;

    // Intent extraction commands
    internal string SystemIntentPrompt => this._promptsConfig.SystemIntent;
    internal string SystemIntentContinuationPrompt => this._promptsConfig.SystemIntentContinuation;

    internal string[] SystemIntentPromptComponents => new string[]
    {
        this.SystemDescriptionPrompt,
        this.SystemIntentPrompt,
        "{{ChatSkill.ExtractChatHistory}}",
        this.SystemIntentContinuationPrompt
    };

    internal string SystemIntentExtractionPrompt => string.Join("\n", this.SystemIntentPromptComponents);

    // Memory extraction commands
    internal string SystemCognitivePrompt => this._promptsConfig.SystemCognitive;
    internal string MemoryFormat => this._promptsConfig.MemoryFormat;
    internal string MemoryAntiHallucination => this._promptsConfig.MemoryAntiHallucination;
    internal string MemoryContinuationPrompt => this._promptsConfig.MemoryContinuation;

    // Long-term memory
    internal string LongTermMemoryName => this._promptsConfig.LongTermMemoryName;
    internal string LongTermMemoryExtractionPrompt => this._promptsConfig.LongTermMemoryExtraction;

    internal string[] LongTermMemoryPromptComponents => new string[]
    {
        this.SystemCognitivePrompt,
        $"{this.LongTermMemoryName} Description:\n{this.LongTermMemoryExtractionPrompt}",
        this.MemoryAntiHallucination,
        $"Chat Description:\n{this.SystemDescriptionPrompt}",
        "{{ChatSkill.ExtractChatHistory}}",
        this.MemoryContinuationPrompt
    };

    internal string LongTermMemoryPrompt => string.Join("\n", this.LongTermMemoryPromptComponents);

    // Working memory
    internal string WorkingMemoryName => this._promptsConfig.WorkingMemoryName;
    internal string WorkingMemoryExtractionPrompt => this._promptsConfig.WorkingMemoryExtraction;

    internal string[] WorkingMemoryPromptComponents => new string[]
    {
        this.SystemCognitivePrompt,
        $"{this.WorkingMemoryName} Description:\n{this.WorkingMemoryExtractionPrompt}",
        this.MemoryAntiHallucination,
        $"Chat Description:\n{this.SystemDescriptionPrompt}",
        "{{ChatSkill.ExtractChatHistory}}",
        this.MemoryContinuationPrompt
    };

    internal string WorkingMemoryPrompt => string.Join("\n", this.WorkingMemoryPromptComponents);

    // Memory map
    internal IDictionary<string, string> MemoryMap => new Dictionary<string, string>()
    {
        { this.LongTermMemoryName, this.LongTermMemoryPrompt },
        { this.WorkingMemoryName, this.WorkingMemoryPrompt }
    };

    // Chat commands
    internal string SystemChatContinuationPrompt = "SINGLE RESPONSE FROM BOT TO USER:\n[{{TimeSkill.Now}} {{timeSkill.Second}}] bot:";

    internal string[] SystemChatPromptComponents => new string[]
    {
        this.SystemDescriptionPrompt,
        this.SystemResponsePrompt,
        "{{$userIntent}}",
        "{{ChatSkill.ExtractUserMemories}}",
        "{{DocumentMemorySkill.QueryDocuments $INPUT}}",
        "{{ChatSkill.AcquireExternalInformation}}",
        "{{ChatSkill.ExtractChatHistory}}",
        this.SystemChatContinuationPrompt
    };

    internal string SystemChatPrompt => string.Join("\n", this.SystemChatPromptComponents);

    internal double ResponseTemperature { get; } = 0.7;
    internal double ResponseTopP { get; } = 1;
    internal double ResponsePresencePenalty { get; } = 0.5;
    internal double ResponseFrequencyPenalty { get; } = 0.5;

    internal double IntentTemperature { get; } = 0.7;
    internal double IntentTopP { get; } = 1;
    internal double IntentPresencePenalty { get; } = 0.5;
    internal double IntentFrequencyPenalty { get; } = 0.5;
};
