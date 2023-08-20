// Copyright (c) Microsoft. All rights reserved.
// ReSharper disable InconsistentNaming
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

using System.Runtime.CompilerServices;
using Extensions;
using global::Connectors.AI.SourceGraph;
using Models;
using StrawberryShake;


/// <summary>
///   This class is used to make GraphQL requests to the SourceGraph Graph API.
/// </summary>
public class SourceGraphGraphQLClient : ISourceGraphQLClient
{
    private readonly ISourceGraphClient _sourceGraphClient;


    /// <summary>
    ///  Initializes a new instance of the <see cref="SourceGraphGraphQLClient"/> class.
    /// </summary>
    /// <param name="sourceGraphClient"></param>
    public SourceGraphGraphQLClient(ISourceGraphClient sourceGraphClient) => _sourceGraphClient = sourceGraphClient;


    /// <inheritdoc />
    public async Task<string?> GetRepoIdAsync(string repoName, CancellationToken cancellationToken)
    {
        IOperationResult<IRepositoryIdQueryResult> queryResponse = await _sourceGraphClient.RepositoryIdQuery.ExecuteAsync(repoName, cancellationToken).ConfigureAwait(false);
        queryResponse.EnsureNoErrors();
        var repositoryId = queryResponse.Data?.Repository?.Id;
        return repositoryId;
    }


    /// <inheritdoc />
    public async IAsyncEnumerable<string>? GetRepoIds(IEnumerable<string> repoNames, int count, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IOperationResult<IRepositoryIdsQueryResult> queryResponse = await _sourceGraphClient.RepositoryIdsQuery.ExecuteAsync((IReadOnlyList<string>)repoNames, count, cancellationToken).ConfigureAwait(false);
        queryResponse.EnsureNoErrors();

        if (queryResponse.Data?.Repositories.Nodes == null)
        {
            yield break;
        }

        foreach (var repo in queryResponse.Data.Repositories.Nodes)
        {
            yield return repo.Id;
        }
    }


    /// <inheritdoc />
    public async Task<IEnumerable<string>?> GetRepoNamesAsync(int count, CancellationToken cancellationToken = default)
    {
        IOperationResult<IRepositoryNamesQueryResult> queryResponse = await _sourceGraphClient.RepositoryNamesQuery.ExecuteAsync(count, cancellationToken).ConfigureAwait(false);
        queryResponse.EnsureNoErrors();
        IEnumerable<string>? repositoryNames = queryResponse.Data?.Repositories?.Nodes?.Select(n => n.Name);
        return repositoryNames;
    }


    /// <inheritdoc />
    public async Task<Repository?> GetRepositoryAsync(string repoName, CancellationToken cancellationToken = default)
    {
        IOperationResult<IRepositoryQueryResult> queryResponse = await _sourceGraphClient.RepositoryQuery.ExecuteAsync(repoName, cancellationToken).ConfigureAwait(false);
        queryResponse.EnsureNoErrors();
        var response = queryResponse.ToSourceGraphResponse();

        return response.Data.Repository;
    }


    /// <inheritdoc />
    public async Task<bool> GetRepositoryEmbeddingExistsAsync(string repoName, CancellationToken cancellationToken = default)
    {
        IOperationResult<IRepositoryEmbeddingsExistQueryResult> queryResponse = await _sourceGraphClient.RepositoryEmbeddingsExistQuery.ExecuteAsync(repoName, cancellationToken).ConfigureAwait(false);
        queryResponse.EnsureNoErrors();
        return queryResponse.Data?.Repository?.EmbeddingExists ?? false;
    }


    /// <inheritdoc />
    public async Task<bool> IsContextRequiredAsync(string query, CancellationToken cancellationToken = default)
    {
        IOperationResult<IIsContextRequiredForChatQueryResult> queryResponse = await _sourceGraphClient.IsContextRequiredForChatQuery.ExecuteAsync(query, cancellationToken).ConfigureAwait(false);
        queryResponse.EnsureNoErrors();
        return queryResponse.Data?.IsContextRequiredForChatQuery ?? false;
    }


    /// <inheritdoc />
    public async IAsyncEnumerable<FileElement> GetRepositoryListOfFilesAsync(string repoName, string branchName = "main", string directory = "src", [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IOperationResult<IRepositoryFilesQueryResult> queryResponse = await _sourceGraphClient.RepositoryFilesQuery.ExecuteAsync(repoName, branchName, directory, cancellationToken).ConfigureAwait(true);
        queryResponse.EnsureNoErrors();

        var response = queryResponse.ToSourceGraphResponse();

        foreach (var file in response.Data.Repository.Branches.Nodes[0].Target.Commit.Tree.Files)
        {
            yield return file;
        }
    }


    /// <inheritdoc />
    public async Task<string?> GetRepositoryFileContentAsync(string repoName, string filePath, CancellationToken cancellationToken = default)
    {
        IOperationResult<IRepositoryFileContentQueryResult> queryResponse = await _sourceGraphClient.RepositoryFileContentQuery.ExecuteAsync(repoName, filePath, cancellationToken).ConfigureAwait(false);
        return queryResponse.Data?.Repository?.DefaultBranch?.Target.Commit?.Blob?.Content;
    }


    /// <inheritdoc />
    public async IAsyncEnumerable<Node> GetSymbolReferencesAsync(string repoName, string symbolName, bool includeContent, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Symbols symbols = new();

        if (!includeContent)
        {
            IOperationResult<ISymbolReferenceQueryResult> queryResponse = await _sourceGraphClient.SymbolReferenceQuery.ExecuteAsync(repoName, symbolName, cancellationToken).ConfigureAwait(false);
            var response = queryResponse.ToSourceGraphResponse();
            symbols = response.Data.Repository.DefaultBranch.Target.Commit.Symbols;
        }

        else
        {
            IOperationResult<ISymbolReferenceFilesQueryResult> queryResponse = await _sourceGraphClient.SymbolReferenceFilesQuery.ExecuteAsync(repoName, symbolName, cancellationToken).ConfigureAwait(false);
            var response = queryResponse.ToSourceGraphResponse();
            symbols = response.Data.Repository.DefaultBranch.Target.Commit.Symbols;
        }

        foreach (var symbol in symbols.Nodes)
        {
            yield return symbol;
        }
    }


    /// <inheritdoc />
    public async IAsyncEnumerable<CodeContext>? GetCodeContextAsync(IEnumerable<string> repos, string query, int codeResultsCount, int textResultsCount, CancellationToken cancellationToken = default)
    {
        IOperationResult<IGetCodyContextResult> queryResponse = await _sourceGraphClient.GetCodyContext.ExecuteAsync((IReadOnlyList<string>)repos, query, codeResultsCount, textResultsCount, cancellationToken).ConfigureAwait(false);
        IEnumerable<CodeContext> codeContexts = queryResponse.ToSourceGraphResponse();

        foreach (var context in codeContexts)
        {
            yield return context;
        }
    }


    /// <inheritdoc />
    public async Task<SnippetAttribution?> GetSnippetAttributionAsync(string snippet, CancellationToken cancellationToken = default) => null;

}
