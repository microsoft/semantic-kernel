// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ModelDiscovery;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
[System.Diagnostics.CodeAnalysis.SuppressMessage("Build", "CA1812:'AzureModelInfo' is an internal class that is apparently never instantiated.", Justification = "JSON object")]
internal sealed class AzureDeploymentInfo
{
    /// <summary>
    /// The OpenAI model to deploy. Can be a base model or a fine tune.
    /// </summary>
    [JsonPropertyName("model")]
    public string Model { get; set; }

    /// <summary>
    /// The owner of this deployment. For Azure OpenAI only "organization-owner" is supported.
    /// </summary>
    [JsonPropertyName("owner")]
    public string Owner { get; set; }

    /// <summary>
    /// The identity of this item.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// The state of a job or item.
    /// </summary>
    [JsonPropertyName("status")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public OperationState Status { get; set; }

    internal enum OperationState
    {
        Canceled,
        Deleted,
        Failed,
        NotRunning,
        Running,
        Succeeded
    }
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
