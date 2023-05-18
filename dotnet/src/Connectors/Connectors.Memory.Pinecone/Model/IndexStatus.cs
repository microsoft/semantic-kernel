// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// Status of the index.
/// </summary>
public class IndexStatus
{
    /// <summary>
    /// Initializes a new instance of the <see cref="IndexStatus" /> class.
    /// </summary>
    /// <param name="host">host.</param>
    /// <param name="port">port.</param>
    /// <param name="state">state.</param>
    /// <param name="ready">ready.</param>
    [JsonConstructor]
    public IndexStatus(string host, int port = default, IndexState? state = default, bool ready = false)
    {
        this.Host = host;
        this.Port = port;
        this.State = state;
        this.Ready = ready;
    }

    /// <summary>
    /// Gets or Sets State
    /// </summary>
    [JsonPropertyName("state")]
    public IndexState? State { get; set; }

    /// <summary>
    /// Gets or Sets Host
    /// </summary>
    [JsonPropertyName("host")]
    public string Host { get; set; }

    /// <summary>
    /// Gets or Sets Port
    /// </summary>
    [JsonPropertyName("port")]
    public int Port { get; set; }

    /// <summary>
    /// Gets or Sets Ready
    /// </summary>
    [JsonPropertyName("ready")]
    public bool Ready { get; set; }
}
