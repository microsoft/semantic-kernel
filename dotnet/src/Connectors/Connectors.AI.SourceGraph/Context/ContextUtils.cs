// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Context;

using Models;


public static class ContextUtils
{
    /// <summary>
    /// Returns list of context messages for a given query, sorted in *reverse* order of importance (that is,
    /// the most important context message appears * last *)
    /// </summary>
    /// <param name="keywordResults"></param>
    /// <param name="filenameResults"></param>
    /// <returns></returns>
    public static ContextResult[] MergeContextResults(ContextResult[] keywordResults, ContextResult[] filenameResults)
    {
        // Take only the last filename result to avoid dominating keyword results
        ContextResult[] lastFilenameResult = filenameResults.Length > 0
            ? new[] { filenameResults[filenameResults.Length - 1] }
            : Array.Empty<ContextResult>();

        List<ContextResult> merged = lastFilenameResult.Concat(keywordResults).ToList();

        Dictionary<string, ContextResult> uniques = new();

        foreach (var result in merged)
        {
            uniques[result.FileName] = result;
        }

        return uniques.Values.ToArray();
    }


    public static List<FileResult> GroupResultsByFile(List<EmbeddingsResult> results)
    {
        List<FileContext> originalFileOrder = new();

        foreach (var result in results.Where(result => originalFileOrder.All(ogFile => ogFile.FileName != result.FileName)))
        {
            originalFileOrder.Add(new FileContext() { FileName = result.FileName, RepoName = result.RepoName, Revision = result.Revision });
        }

        Dictionary<string, List<EmbeddingsResult>> resultsGroupedByFile = new();

        foreach (var result in results)
        {
            if (!resultsGroupedByFile.ContainsKey(result.FileName!))
            {
                resultsGroupedByFile[result.FileName!] = new List<EmbeddingsResult> { result };
            }
            else
            {
                resultsGroupedByFile[result.FileName!].Add(result);
            }
        }

        return originalFileOrder.Select(file => new FileResult
        {
            FileContext = file,
            Results = MergeConsecutiveResults(resultsGroupedByFile[file.FileName])?.ToArray()
        }).ToList();
    }


    private static List<string>? MergeConsecutiveResults(IEnumerable<EmbeddingsResult> results)
    {
        List<EmbeddingsResult> sortedResults = results.OrderBy(r => r.StartLine).ToList();

        var content = sortedResults[0].Content;

        if (content == null)
        {
            return null;
        }

        List<string> mergedResults = new()
        {
            content
        };

        for (var i = 1; i < sortedResults.Count; i++)
        {
            var result = sortedResults[i];
            var previousResult = sortedResults[i - 1];

            if (result.StartLine == previousResult.EndLine)
            {
                mergedResults[mergedResults.Count - 1] += result.Content;
            }
            else
            {
                if (result.Content != null)
                {
                    mergedResults.Add(result.Content);
                }
            }
        }

        return mergedResults;

    }
}
