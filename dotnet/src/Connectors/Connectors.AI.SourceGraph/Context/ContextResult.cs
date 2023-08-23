// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Context;

using Models;


public class ContextResult
{
    public string? RepoName { get; set; }
    public string? Revision { get; set; }
    public string? FileName { get; set; }
    public string? Content { get; set; }

    public long? StartLine { get; set; }

    public long? EndLine { get; set; }
    public string? Language { get; set; }


    public static implicit operator ContextResult(EmbeddingsResult result) => new()
    {
        RepoName = result.RepoName,
        Revision = result.Revision,
        FileName = result.FileName,
        Content = result.Content,
        StartLine = result.StartLine,
        EndLine = result.EndLine,
        Language = Path.GetExtension(result.FileName)
    };


    public static implicit operator ContextResult(CodeContext codeContext) => new()
    {
        RepoName = codeContext.Blob.Repository?.Name,
        Revision = codeContext.Blob.Commit?.Oid,
        FileName = Path.GetFileName(codeContext.Blob.Path),
        Content = codeContext.ChunkContent,
        StartLine = codeContext.StartLine,
        EndLine = codeContext.EndLine,
        Language = codeContext.Blob.Repository?.Language
    };
}
