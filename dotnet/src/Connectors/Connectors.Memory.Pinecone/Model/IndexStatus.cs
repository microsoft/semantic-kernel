using System.Text;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// IndexStatus
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

    /// <summary>
    /// Returns the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()
    {
        StringBuilder sb = new();
        sb.Append("class IndexStatus {\n");
        sb.Append("  Host: ").Append(this.Host).Append('\n');
        sb.Append("  Port: ").Append(this.Port).Append('\n');
        sb.Append("  State: ").Append(this.State).Append('\n');
        sb.Append("  Ready: ").Append(this.Ready).Append('\n');
        sb.Append("}\n");
        return sb.ToString();
    }

}
