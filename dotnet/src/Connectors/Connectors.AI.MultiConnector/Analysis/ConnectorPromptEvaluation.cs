// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

/// <summary>
/// Represents the evaluation of a connector prompt test by a vetting connector, validating if the prompt's response is acceptable.
/// </summary>
public class ConnectorPromptEvaluation : TestEvent
{
    public override string DebuggerDisplay => $"{base.DebuggerDisplay}, Tested {this.Test.ConnectorName}, Vetted: {this.IsVetted}, Prompt: {PromptSignature.GeneratePromptLog(this.Test.Prompt, 20, Defaults.TruncatedLogFormat, true)}, Result: {PromptSignature.GeneratePromptLog(this.Test.Result, 20, Defaults.TruncatedLogFormat, true)}";

    /// <summary>
    /// The connector test to be evaluated
    /// </summary>
    public ConnectorTest Test { get; set; } = new();

    /// <summary>
    /// The name of the vetting connector.
    /// </summary>
    public string VettingConnector { get; set; } = "";

    /// <summary>
    /// The result of the evaluation.
    /// </summary>
    public bool IsVetted { get; set; }
}
