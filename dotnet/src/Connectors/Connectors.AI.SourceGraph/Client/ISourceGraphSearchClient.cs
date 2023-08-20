// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

using global::Connectors.AI.SourceGraph;


/// <summary>
///   Client for conducting search queries against SourceGraph GraphQL API.
/// </summary>
public interface ISourceGraphSearchClient
{

    Task<SearchResult?> SearchAsync(string query, CancellationToken cancellationToken = default);


    /// <summary>
    /// Does an embeddings search for the given natural language query in the given repositories.
    /// </summary>
    /// <param name="repoId"></param>
    /// <param name="query"></param>
    /// <param name="codeResultsCount"></param>
    /// <param name="textResultsCount"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<EmbeddingsSearch?> SearchEmbeddingsAsync(string repoId, string query, int codeResultsCount, int textResultsCount, CancellationToken cancellationToken = default);


    /// <summary>
    /// Does an embeddings search for the given natural language query in the given repositories.
    /// </summary>
    /// <param name="repoIds"></param>
    /// <param name="query"></param>
    /// <param name="codeResultsCount"></param>
    /// <param name="textResultsCount"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<EmbeddingsSearch?> EmbeddingsSearchAsync(IEnumerable<string> repoIds, string query, int codeResultsCount, int textResultsCount, CancellationToken cancellationToken = default);
}
