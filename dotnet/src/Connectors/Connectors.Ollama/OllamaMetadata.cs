// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Runtime.CompilerServices;
using OllamaSharp.Models;
using OllamaSharp.Models.Chat;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents the metadata of the Ollama response.
/// </summary>
public sealed class OllamaMetadata : ReadOnlyDictionary<string, object?>
{
    internal OllamaMetadata(GenerateCompletionDoneResponseStream ollamaResponse) : base(new Dictionary<string, object?>())
    {
        this.TotalDuration = ollamaResponse.TotalDuration;
        this.EvalCount = ollamaResponse.EvalCount;
        this.EvalDuration = ollamaResponse.EvalDuration;
        this.CreatedAt = ollamaResponse.CreatedAt;
        this.LoadDuration = ollamaResponse.LoadDuration;
        this.PromptEvalCount = ollamaResponse.PromptEvalCount;
        this.PromptEvalDuration = ollamaResponse.PromptEvalDuration;
        this.Done = ollamaResponse.Done;
    }

    internal OllamaMetadata(ChatResponse response) : base(new Dictionary<string, object?>())
    {
        this.TotalDuration = response.TotalDuration;
        this.EvalCount = response.EvalCount;
        this.EvalDuration = response.EvalDuration;
        this.CreatedAt = response.CreatedAt;
        this.LoadDuration = response.LoadDuration;
        this.PromptEvalDuration = response.PromptEvalDuration;
        this.CreatedAt = response.CreatedAt;
    }

    internal OllamaMetadata(ChatResponseStream message) : base(new Dictionary<string, object?>())
    {
        this.CreatedAt = message.CreatedAt;
        this.Done = message.Done;
    }

    /// <summary>
    /// Time spent in nanoseconds evaluating the prompt
    /// </summary>
    public long PromptEvalDuration
    {
        get => this.GetValueFromDictionary() as long? ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Number of tokens in the prompt
    /// </summary>
    public int PromptEvalCount
    {
        get => this.GetValueFromDictionary() as int? ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Time spent in nanoseconds loading the model
    /// </summary>
    public long LoadDuration
    {
        get => this.GetValueFromDictionary() as long? ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Returns the prompt's feedback related to the content filters.
    /// </summary>
    public string? CreatedAt
    {
        get => this.GetValueFromDictionary() as string;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Time in nano seconds spent generating the response
    /// </summary>
    public long EvalDuration
    {
        get => this.GetValueFromDictionary() as long? ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Number of tokens the response
    /// </summary>
    public int EvalCount
    {
        get => this.GetValueFromDictionary() as int? ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Time spent in nanoseconds generating the response
    /// </summary>
    public long TotalDuration
    {
        get => this.GetValueFromDictionary() as long? ?? 0;
        internal init => this.SetValueInDictionary(value);
    }

    /// <summary>
    /// Informs when the response generation process is complete.
    /// </summary>
    public bool? Done
    {
        get => this.GetValueFromDictionary() as bool?;
        internal init => this.SetValueInDictionary(value);
    }

    private void SetValueInDictionary(object? value, [CallerMemberName] string propertyName = "")
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary([CallerMemberName] string propertyName = "")
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
