namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using System.Text.Json.Serialization;


public class FileMatch
{

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("repository")]
    public Repository Repository { get; set; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("file")]
    public FileElement File { get; set; }


    internal static FileMatch FromSearchResult(ICodeSearchQuery_Search_Results_Results_FileMatch fileMatch)
    {
        return new()
        {
            File = new FileElement()
            {
                Name = fileMatch.File.Name,
                Path = fileMatch.File.Path,
                Url = fileMatch.File.Url,
                Content = fileMatch.File.Content,
                Commit = new Commit()
                {
                    Oid = fileMatch.File.Commit.Oid
                }
            },
            Repository = new Repository()
            {
                Name = fileMatch.File.Repository.Name,
                Id = fileMatch.File.Repository.Id,
                Description = fileMatch.File.Repository.Description,
                Language = fileMatch.File.Repository.Language,
                Stars = fileMatch.File.Repository.Stars,
                Url = fileMatch.File.Repository.Url
            }
        };
    }
}
