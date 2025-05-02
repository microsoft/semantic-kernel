namespace SemanticKernel.HelloAgents.Internal;

/// <summary>
/// Corresponds with project settings to access Azure AI Services.
/// </summary>
internal sealed class FoundrySettings
{
    public const string Section = "AzureOpenAI";
    public const string ConnectionStringSetting = "AzureAI:ConnectionString";

    /// <summary>
    /// The name of the model deployment to target.
    /// </summary>
    public string ChatDeploymentName { get; init; } = string.Empty;

    /// <summary>
    /// The connection string for a Foundry Project.  Required for an Azure AI Agent
    /// or discovering AI services through a Foundry Connection.
    /// </summary>
    public string ConnectionString { get; internal set; } = string.Empty;

    /// <summary>
    /// The endpoint for Azure AI Services.  Required to access Azure AI Services
    /// when a Foundry Project connection string is not defined..
    /// </summary>
    public string Endpoint { get; init; } = string.Empty;

    /// <summary>
    /// An optional API key associated with the Azure AI Services endpoint (<see cref="Endpoint"/>).
    /// Use token credentials when not defined.
    /// </summary>
    public string ApiKey { get; init; } = string.Empty;
}
