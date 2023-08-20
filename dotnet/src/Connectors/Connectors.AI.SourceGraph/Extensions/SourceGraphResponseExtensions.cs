// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Extensions;

using System.Text.Json;
using global::Connectors.AI.SourceGraph;
using StrawberryShake;


/// <summary>
///  Extensions for converting GraphQL responses to SourceGraphResponse objects.
/// </summary>
public static class SourceGraphResponseExtensions
{
    /// <summary>
    ///  Converts a GraphQL response to a SourceGraphResponse object.
    /// </summary>
    /// <param name="queryResponse"></param>
    /// <returns></returns>
    public static SourceGraphResponse ToSourceGraphResponse(this IOperationResult queryResponse)
        => SourceGraphResponse.FromJson(JsonSerializer.Serialize(queryResponse, typeof(object), new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase }));


    /// <summary>
    ///  Converts a GraphQL response to a SourceGraphResponse object.
    /// </summary>
    /// <param name="queryResponse"></param>
    /// <returns></returns>
    public static IEnumerable<CodeContext> ToSourceGraphResponse(this IOperationResult<IGetCodyContextResult> queryResponse)
    {
        IEnumerable<IGetCodyContext_GetCodyContext_FileChunkContext>? contexts = queryResponse.Data?.GetCodyContext.OfType<IGetCodyContext_GetCodyContext_FileChunkContext>();
        return contexts?.Select(CodeContext.FromFileChunkContext) ?? Enumerable.Empty<CodeContext>();
    }


    /// <summary>
    ///  Converts a GraphQL response to a SourceGraphResponse object.
    /// </summary>
    /// <param name="queryResponse"></param>
    /// <returns></returns>
    public static SearchResult? ToSearchResult(this IOperationResult<ICodeSearchQueryResult> queryResponse)
    {
        if (queryResponse.Errors?.Any() == true || queryResponse.Data?.Search?.Results == null)
        {
            return null;
        }
        return SearchResult.FromSearchResults(queryResponse.Data.Search.Results);
    }
}
