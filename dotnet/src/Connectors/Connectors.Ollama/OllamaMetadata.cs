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
    internal OllamaMetadata(GenerateCompletionResponseStream? ollamaResponse) : base(new Dictionary<string, object?>())
    {
        if (ollamaResponse is null)
        {
            return;
        }

        this.CreatedAt = ollamaResponse.CreatedAt;
        this.Done = ollamaResponse.Done;

        if (ollamaResponse is GenerateCompletionDoneResponseStream doneResponse)
        {
            this.TotalDuration = doneResponse.TotalDuration;
            this.EvalCount = doneResponse.EvalCount;
            this.EvalDuration = doneResponse.EvalDuration;
            this.LoadDuration = doneResponse.LoadDuration;
            this.PromptEvalCount = doneResponse.PromptEvalCount;
            this.PromptEvalDuration = doneResponse.PromptEvalDuration;
        }
    }

    internal OllamaMetadata(ChatResponseStream? message) : base(new Dictionary<string, object?>())
    {
        if (message is null)
        {
            return;
        }
        this.CreatedAt = message?.CreatedAt;
        this.Done = message?.Done;

        if (message is ChatDoneResponseStream doneMessage)
        {
            this.TotalDuration = doneMessage.TotalDuration;
            this.EvalCount = doneMessage.EvalCount;
            this.EvalDuration = doneMessage.EvalDuration;
            this.LoadDuration = doneMessage.LoadDuration;
            this.PromptEvalCount = doneMessage.PromptEvalCount;
            this.PromptEvalDuration = doneMessage.PromptEvalDuration;
        }
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
    /// The response is done
    /// </summary>
    public bool? Done
    {
        get => this.GetValueFromDictionary() as bool?;
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

    private void SetValueInDictionary(object? value, [CallerMemberName] string propertyName = "")
        => this.Dictionary[propertyName] = value;

    private object? GetValueFromDictionary([CallerMemberName] string propertyName = "")
        => this.Dictionary.TryGetValue(propertyName, out var value) ? value : null;
}
