// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;

/// <summary>
/// Represents the settings for multiple connectors associated with a particular type of prompt.
/// </summary>
public class PromptMultiConnectorSettings
{
    /// <summary>
    /// Gets or sets the type of prompt associated with these settings.
    /// </summary>
    public PromptType PromptType { get; set; } = new();

    /// <summary>
    /// Choose whether to apply the model specific transforms for this prompt type
    /// </summary>
    public bool ApplyModelTransform { get; set; }

    /// <summary>
    /// Optionally transform the input prompt specifically
    /// </summary>
    public PromptTransform? PromptTypeTransform { get; set; }

    /// <summary>
    /// Gets a dictionary mapping connector names to their associated settings for this prompt type.
    /// </summary>
    public Dictionary<string, PromptConnectorSettings> ConnectorSettingsDictionary { get; } = new();

    /// <summary>
    /// Retrieves the settings associated with a specific connector for the prompt type.
    /// </summary>
    /// <param name="connectorName">The name of the connector.</param>
    /// <returns>The <see cref="PromptConnectorSettings"/> associated with the given connector name.</returns>
    public PromptConnectorSettings GetConnectorSettings(string connectorName)
    {
        if (!this.ConnectorSettingsDictionary.TryGetValue(connectorName, out var promptConnectorSettings))
        {
            promptConnectorSettings = new PromptConnectorSettings();
            this.ConnectorSettingsDictionary[connectorName] = promptConnectorSettings;
        }

        return promptConnectorSettings;
    }

    /// <summary>
    /// Selects the appropriate text completion to use based on the vetting evaluations analyzed.
    /// </summary>
    /// <param name="completionJob">The prompt and request settings to find the appropriate completion for</param>
    /// <param name="namedTextCompletions">The list of available text completions.</param>
    /// <param name="settingsConnectorComparer"></param>
    /// <returns>The selected <see cref="NamedTextCompletion"/>.</returns>
    public (NamedTextCompletion namedTextCompletion, PromptConnectorSettings promptConnectorSettings) SelectAppropriateTextCompletion(CompletionJob completionJob, IReadOnlyList<NamedTextCompletion> namedTextCompletions, Func<CompletionJob, PromptConnectorSettings, PromptConnectorSettings, int> settingsConnectorComparer)
    {
        var filteredConnectors = new List<(NamedTextCompletion textCompletion, PromptConnectorSettings promptConnectorSettings)>();
        foreach (var namedTextCompletion in namedTextCompletions)
        {
            var promptConnectorSettings = this.GetConnectorSettings(namedTextCompletion.Name);
            if (promptConnectorSettings.VettingLevel > 0)
            {
                filteredConnectors.Add((namedTextCompletion, promptConnectorSettings));
            }
        }

        if (filteredConnectors.Count > 0)
        {
            filteredConnectors.Sort((c1, c2) => settingsConnectorComparer(completionJob, c1.Item2, c2.Item2));
            return filteredConnectors[0];
        }

        // if no vetted connector is found, return the first primary one
        var primaryConnectorSettings = this.GetConnectorSettings(namedTextCompletions[0].Name);
        return (namedTextCompletions[0], primaryConnectorSettings);
    }

    public void AddSessionPrompt(string prompt)
    {
        this._currentSessionPrompts[prompt] = true;
    }

    private readonly ConcurrentDictionary<string, bool> _currentSessionPrompts = new();

    internal bool IsTestingNeeded(string prompt, IReadOnlyList<NamedTextCompletion> namedTextCompletions, bool isNewPrompt)
    {
        return (isNewPrompt
                || (this.PromptType.Instances.Count < this.PromptType.MaxInstanceNb
                    && !this.PromptType.Instances.Contains(prompt)))
               && !this._currentSessionPrompts.ContainsKey(prompt)
               && namedTextCompletions.Any(namedTextCompletion =>
                   !this.ConnectorSettingsDictionary.TryGetValue(namedTextCompletion.Name, out PromptConnectorSettings? value)
                   || value?.VettingLevel == 0);
    }

    internal IEnumerable<NamedTextCompletion> GetCompletionsToTest(ConnectorTest originalTest, IReadOnlyList<NamedTextCompletion> namedTextCompletions)
    {
        return namedTextCompletions.Where(namedTextCompletion => namedTextCompletion.Name != originalTest.ConnectorName
                                                                 && (!this.ConnectorSettingsDictionary.TryGetValue(namedTextCompletion.Name, out PromptConnectorSettings value)
                                                                     || value.VettingLevel == 0));
    }
}
