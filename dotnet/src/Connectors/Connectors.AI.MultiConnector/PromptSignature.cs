// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Identifies a type of prompts from its beginning and a subset of parameters.
/// </summary>
public class PromptSignature
{
    private Regex? _compiledRegex;
    private const float FloatComparisonTolerance = 2 * float.Epsilon;

    /// <summary>
    /// Gets or sets the request settings supplied with the prompt on a completion call.
    /// </summary>
    public CompleteRequestSettings RequestSettings { get; set; }

    /// <summary>
    /// First chars of a prompt that identify its type while staying the same between different calls.
    /// </summary>
    public string TextBeginning { get; set; }

    /// <summary>
    /// optional regular expression pattern for matching complex prompts.
    /// </summary>
    public string? MatchingRegex { get; set; }

    private Regex? CompiledRegex
    {
        get
        {
            if (this._compiledRegex == null && this.MatchingRegex?.Length > 0)
            {
                this._compiledRegex = new Regex(this.MatchingRegex, RegexOptions.Compiled | RegexOptions.IgnoreCase);
            }

            return this._compiledRegex;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptSignature"/> class.
    /// </summary>
    public PromptSignature()
    {
        this.RequestSettings = new();
        this.TextBeginning = string.Empty;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptSignature"/> class.
    /// </summary>
    /// <param name="requestSettings">The request settings for the prompt.</param>
    /// <param name="textBeginning">The beginning of the text to identify the prompt type.</param>
    public PromptSignature(CompleteRequestSettings requestSettings, string textBeginning)
    {
        this.RequestSettings = requestSettings;
        this.TextBeginning = textBeginning;
    }

    /// <summary>
    /// Extracts a <see cref="PromptSignature"/> from a prompt string and request settings.
    /// </summary>
    /// <param name="prompt">The prompt string.</param>
    /// <param name="settings">The request settings associated with the prompt</param>
    /// <param name="truncationLength">The length of the extracted beginning of the prompt for identification.</param>
    /// <returns>The extracted <see cref="PromptSignature"/>.</returns>
    public static PromptSignature ExtractFromPrompt(string prompt, CompleteRequestSettings settings, int truncationLength)
    {
        return new PromptSignature(settings, prompt.Substring(0, truncationLength));
    }

    /// <summary>
    /// Determines if the prompt matches the <see cref="PromptSignature"/>.
    /// </summary>
    /// <param name="prompt">The prompt string.</param>
    /// <param name="promptSettings">The request settings for the prompt.</param>
    /// <returns><c>true</c> if the prompt matches the <see cref="PromptSignature"/>; otherwise, <c>false</c>.</returns>
    public bool Matches(string prompt, CompleteRequestSettings promptSettings)
    {
        return (this.MatchSettings(promptSettings) && (this.CompiledRegex?.IsMatch(prompt) ??
                                                       prompt.StartsWith(this.TextBeginning, StringComparison.OrdinalIgnoreCase)));
    }

    private bool MatchSettings(CompleteRequestSettings promptSettings)
    {
        return this.RequestSettings.MaxTokens == promptSettings.MaxTokens &&
               Math.Abs(this.RequestSettings.Temperature - promptSettings.Temperature) < FloatComparisonTolerance &&
               Math.Abs(this.RequestSettings.TopP - promptSettings.TopP) < FloatComparisonTolerance &&
               this.RequestSettings.StopSequences.SequenceEqual(promptSettings.StopSequences) &&
               Math.Abs(this.RequestSettings.PresencePenalty - promptSettings.PresencePenalty) < FloatComparisonTolerance &&
               Math.Abs(this.RequestSettings.FrequencyPenalty - promptSettings.FrequencyPenalty) < FloatComparisonTolerance &&
               this.RequestSettings.ChatSystemPrompt == promptSettings.ChatSystemPrompt &&
               this.RequestSettings.ResultsPerPrompt == promptSettings.ResultsPerPrompt;
    }
}
