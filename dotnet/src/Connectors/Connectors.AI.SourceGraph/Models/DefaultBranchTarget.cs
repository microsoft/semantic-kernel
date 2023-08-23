namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using System.Text.Json.Serialization;


public class DefaultBranchTarget
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("commit")]
    public Commit? Commit { get; set; }
}
