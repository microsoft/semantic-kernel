namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using System.Text.Json.Serialization;


public class Blob
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("path")]
    public string? Path { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("repository")]
    public Repository? Repository { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("commit")]
    public Commit? Commit { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("content")]
    public string? Content { get; set; }


    internal static Blob FromFileChunkContextBlob(IGetCodyContext_GetCodyContext_FileChunkContext blob)
    {
        return new Blob()
        {
            Path = blob.Blob.Path,
            Repository = new Repository()
            {
                Name = blob.Blob.Repository.Name,
                Id = blob.Blob.Repository.Id
            },
            Commit = new Commit()
            {
                Id = blob.Blob.Commit.Id,
                Oid = blob.Blob.Commit.Oid
            }
        };
    }
}
