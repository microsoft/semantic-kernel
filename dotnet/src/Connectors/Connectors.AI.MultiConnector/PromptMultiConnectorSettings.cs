// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

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
    /// Gets a dictionary mapping connector names to their associated settings for this prompt type.
    /// </summary>
    public Dictionary<string, PromptConnectorSettings> ConnectorSettingsDictionary { get; } = new();

    /// <summary>
    /// A flag to keep track of when the prompt type is being tested to prevent multiple executions.
    /// </summary>
    internal bool IsTesting;

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
    /// <param name="namedTextCompletions">The list of available text completions.</param>
    /// <param name="settingsConnectorComparer"></param>
    /// <returns>The selected <see cref="NamedTextCompletion"/>.</returns>
    public NamedTextCompletion SelectAppropriateTextCompletion(IReadOnlyList<NamedTextCompletion> namedTextCompletions, Func<PromptConnectorSettings, PromptConnectorSettings, int> settingsConnectorComparer)
    {
        var filteredConnectors = new List<(NamedTextCompletion, PromptConnectorSettings)>();
        foreach (var namedTextCompletion in namedTextCompletions)
        {
            if (this.ConnectorSettingsDictionary.TryGetValue(namedTextCompletion.Name, out PromptConnectorSettings? value))
            {
                if (value?.VettingLevel > 0)
                {
                    filteredConnectors.Add((namedTextCompletion, value));
                }
            }
        }

        filteredConnectors.Sort((c1, c2) => settingsConnectorComparer(c1.Item2, c2.Item2));
        if (filteredConnectors.Count > 0)
        {
            return filteredConnectors[0].Item1;
        }

        // if no vetted connector is found, return the first primary one
        return namedTextCompletions[0];
    }

    internal bool IsTestingNeeded(IReadOnlyList<NamedTextCompletion> namedTextCompletions)
    {
        return !this.IsTesting && namedTextCompletions.Any(namedTextCompletion => !this.ConnectorSettingsDictionary.TryGetValue(namedTextCompletion.Name, out PromptConnectorSettings? value) || value?.VettingLevel == 0);
    }

    internal IEnumerable<NamedTextCompletion> GetCompletionsToTest(IReadOnlyList<NamedTextCompletion> namedTextCompletions)
    {
        return namedTextCompletions.Where(namedTextCompletion => !this.ConnectorSettingsDictionary.TryGetValue(namedTextCompletion.Name, out PromptConnectorSettings? value) || value?.VettingLevel == 0);
    }
}
