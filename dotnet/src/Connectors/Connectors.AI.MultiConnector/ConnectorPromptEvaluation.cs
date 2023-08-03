namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents the evaluation of a connector prompt test by a vetting connector, validating if the prompt's reponse is acceptable.
/// </summary>
public class ConnectorPromptEvaluation : TestEvent
{
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