namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using System.Text.Json.Serialization;


public class CodeContext
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("__typename")]
    public string? Typename { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("blob")]
    public Blob Blob { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("startLine")]
    public long? StartLine { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("endLine")]
    public long? EndLine { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("chunkContent")]
    public string? ChunkContent { get; set; }


    internal static CodeContext FromFileChunkContext(IGetCodyContext_GetCodyContext_FileChunkContext fileChunkContext)
    {
        return new CodeContext()
        {
            Blob = Blob.FromFileChunkContextBlob(fileChunkContext),
            StartLine = fileChunkContext.StartLine,
            EndLine = fileChunkContext.EndLine,
            ChunkContent = fileChunkContext.ChunkContent
        };
    }
}
