// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
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
    public string PromptStart { get; set; }

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
        this.PromptStart = string.Empty;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptSignature"/> class.
    /// </summary>
    /// <param name="requestSettings">The request settings for the prompt.</param>
    /// <param name="promptStart">The beginning of the text to identify the prompt type.</param>
    public PromptSignature(CompleteRequestSettings requestSettings, string promptStart)
    {
        this.RequestSettings = requestSettings;
        this.PromptStart = promptStart;
    }

    /// <summary>
    /// Extracts a <see cref="PromptSignature"/> from a prompt string, request settings and existing signatures to deal with overlapping prompt starts.
    /// </summary>
    /// <param name="completionJob">The prompt and request settings to extract a signature from</param>
    /// <param name="promptMultiConnectorSettingsCollection"></param>
    /// <param name="truncationLength">The length of the extracted beginning of the prompt for identification.</param>
    /// <returns>The extracted <see cref="PromptSignature"/>.</returns>
    public static PromptSignature ExtractFromPrompt(CompletionJob completionJob, IEnumerable<PromptMultiConnectorSettings> promptMultiConnectorSettingsCollection, int truncationLength)
    {
        var promptStart = completionJob.Prompt.Substring(0, truncationLength);

        foreach (var promptMultiConnectorSettings in promptMultiConnectorSettingsCollection)
        {
            if (promptMultiConnectorSettings.PromptType.Signature.MatchingRegex != null
                && promptMultiConnectorSettings.PromptType.Signature.PromptStart.StartsWith(promptStart, StringComparison.Ordinal))
            {
                promptStart = PromptSignature.GetCommonPrefix(promptMultiConnectorSettings.PromptType.Signature.PromptStart, completionJob.Prompt);
            }
        }

        return new PromptSignature(completionJob.RequestSettings, promptStart);
    }

    /// <summary>
    /// Extracts a <see cref="PromptSignature"/> from a prompt string, request settings and distinct prompt instance of the same type, increasing from default truncated start to deal with overlapping prompt starts.
    /// </summary>
    public static PromptSignature ExtractFrom2Instances(string prompt1, string prompt2, CompleteRequestSettings settings)
    {
        int staticPartLength = GetCommonPrefix(prompt1, prompt2).Length;

        var newStart = prompt1.Substring(0, staticPartLength);

        return new PromptSignature(settings, newStart);
    }

    /// <summary>
    /// Generates a log for a prompt that is truncated at the beginning and the end.
    /// </summary>
    public static string GeneratePromptLog(string prompt, int truncationLength, string truncatedPromptFormat)
    {
        var promptLog = PromptSignature.GenerateTruncatedString(prompt, truncationLength, true, truncatedPromptFormat);
        return promptLog;
    }

    /// <summary>
    /// Generates a truncated string from input with optional formatting
    /// </summary>
    public static string GenerateTruncatedString(string prompt, int truncationLength, bool bidirectional, string template = "{0}{1}")
    {
        if (prompt.Length <= truncationLength)
        {
            return prompt;
        }

        var promptStart = prompt.Substring(0, truncationLength);
        var promptEnd = bidirectional ? prompt.Substring(prompt.Length - truncationLength, truncationLength) : "";
        var toReturn = string.Format(CultureInfo.InvariantCulture, template, promptStart, promptEnd);
        return toReturn;
    }

    /// <summary>
    /// Gets the common prefix of two strings.
    /// </summary>
    public static string GetCommonPrefix(string prompt1, string prompt2)
    {
        var staticPartLength = 0;

        while (staticPartLength < prompt1.Length && staticPartLength < prompt2.Length &&
               prompt1[staticPartLength] == prompt2[staticPartLength])
        {
            staticPartLength++;
        }

        if (staticPartLength >= prompt1.Length && staticPartLength >= prompt2.Length)
        {
            throw new ArgumentException("The two prompts don't have matching beginnings");
        }

        return prompt1.Substring(0, staticPartLength);
    }

    /// <summary>
    /// Determines if the prompt matches the <see cref="PromptSignature"/>.
    /// </summary>
    /// <param name="completionJob">The prompt and request settings for the completion</param>
    /// <returns><c>true</c> if the prompt matches the <see cref="PromptSignature"/>; otherwise, <c>false</c>.</returns>
    public bool Matches(CompletionJob completionJob)
    {
        return (this.MatchSettings(completionJob.RequestSettings) && (this.CompiledRegex?.IsMatch(completionJob.Prompt) ??
                                                                      completionJob.Prompt.StartsWith(this.PromptStart, StringComparison.Ordinal)));
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
