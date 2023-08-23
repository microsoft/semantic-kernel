namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using System.Text.Json.Serialization;


public class SearchResult
{
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("results")]
    public List<FileMatch>? Results { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("limitHit")]
    public bool? LimitHit { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("matchCount")]
    public long? MatchCount { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("elapsedMilliseconds")]
    public long? ElapsedMilliseconds { get; set; }

    [JsonPropertyName("alert")]
    public object Alert { get; set; }


    internal static SearchResult FromSearchResults(ICodeSearchQuery_Search_Results results)
    {
        return new SearchResult()
        {
            Results = results.Results.OfType<ICodeSearchQuery_Search_Results_Results_FileMatch>().Select(FileMatch.FromSearchResult).ToList(),
            LimitHit = results.LimitHit,
            MatchCount = results.MatchCount,
            ElapsedMilliseconds = results.ElapsedMilliseconds,
            Alert = results.Alert
        };
    }

}
