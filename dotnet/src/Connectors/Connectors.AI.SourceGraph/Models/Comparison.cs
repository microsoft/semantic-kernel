namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using System.Text.Json.Serialization;


public class Comparison
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("commits")]
    public Commits Commits { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("fileDiffs")]
    public FileDiffs FileDiffs { get; set; }
}
