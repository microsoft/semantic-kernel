// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents the settings associated with a particular prompt type and a connector.
/// </summary>
public class PromptConnectorSettings
{
    /// <summary>
    /// the vetting level of the connector against the prompt type
    /// </summary>
    public VettingLevel VettingLevel { get; set; } = VettingLevel.None;

    /// <summary>
    /// the connector that was used to assess the VettingLevel
    /// </summary>
    public string VettingConnector { get; set; } = "";

    /// <summary>
    /// the average duration of the connector's response to the prompt type during evaluations
    /// </summary>
    public TimeSpan AverageDuration { get; set; }

    /// <summary>
    /// the average cost of the connector's calls with the prompt type during evaluations
    /// </summary>
    public decimal AverageCost { get; set; }

    ///// <summary>
    ///// the evaluations that were performed on the connector for the prompt type
    ///// </summary>
    //public List<ConnectorPromptEvaluation> Evaluations { get; set; } = new();
}
