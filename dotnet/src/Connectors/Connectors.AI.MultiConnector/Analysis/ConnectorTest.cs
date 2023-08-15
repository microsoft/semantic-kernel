// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

/// <summary>
/// Represents a test performed on a connector, called with a prompt with its result and duration recorded.
/// </summary>
public class ConnectorTest : TestEvent
{
    public override string DebuggerDisplay => $"{base.DebuggerDisplay}, {this.ConnectorName}, Cost: {this.Cost}, Prompt: {PromptSignature.GeneratePromptLog(this.Prompt, 20, Defaults.TruncatedLogFormat, true)}, Result: {PromptSignature.GeneratePromptLog(this.Result, 20, Defaults.TruncatedLogFormat, true)}";

    /// <summary>
    /// Name of the connector used for the test.
    /// </summary>
    public string ConnectorName { get; set; } = "";

    /// <summary>
    /// Sample prompt used for the test (before connector-specific transforms).
    /// </summary>
    public string Prompt { get; set; } = "";

    /// <summary>
    /// Request settings for the test (before connector-specific adjustments).
    /// </summary>
    public CompleteRequestSettings RequestSettings { get; set; } = new();

    /// <summary>
    /// Result returned by the connector called with the test prompt.
    /// </summary>
    public string Result { get; set; } = "";

    /// <summary>
    /// Cost of the call to the connector computed according to the cost per request and cost per token configured.
    /// </summary>
    public decimal Cost { get; set; }

    /// <summary>
    /// Helper to create connector test from completion components
    /// </summary>
    public static ConnectorTest Create(CompletionJob completionJob, NamedTextCompletion textCompletion, string result, TimeSpan duration, decimal textCompletionCost)
    {
        var connectorTest = new ConnectorTest
        {
            Prompt = completionJob.Prompt,
            RequestSettings = completionJob.RequestSettings,
            ConnectorName = textCompletion.Name,
            Result = result,
            Duration = duration,
            Cost = textCompletionCost,
        };
        return connectorTest;
    }
}
