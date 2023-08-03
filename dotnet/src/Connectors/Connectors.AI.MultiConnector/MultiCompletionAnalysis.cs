using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents the collection of evaluations of connectors against prompt types, to be saved and analyzed.
/// </summary>
public class MultiCompletionAnalysis : TestEvent
{
    /// <summary>
    /// Gets or sets the list of connector prompt evaluations saved in this analysis.
    /// </summary>
    public List<ConnectorPromptEvaluation> Evaluations { get; set; } = new();
}