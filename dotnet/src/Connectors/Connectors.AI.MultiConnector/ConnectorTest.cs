using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents a test performed on a connector, called with a prompt with its result and duration recorded.
/// </summary>
public class ConnectorTest : TestEvent
{
    /// <summary>
    /// name of the connector used for the test.
    /// </summary>
    public string ConnectorName { get; set; } = "";

    /// <summary>
    /// prompt to call the connector with.
    /// </summary>
    public string Prompt { get; set; } = "";

    /// <summary>
    /// request settings for the test.
    /// </summary>
    public CompleteRequestSettings RequestSettings { get; set; } = new();

    /// <summary>
    /// Gets or sets the result returned by the connector called with the test prompt.
    /// </summary>
    public string Result { get; set; } = "";
}