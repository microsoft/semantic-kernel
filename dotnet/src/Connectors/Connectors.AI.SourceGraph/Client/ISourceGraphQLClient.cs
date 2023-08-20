// Copyright (c) Microsoft. All rights reserved.
// ReSharper disable InconsistentNaming
// ReSharper disable MissingBlankLines
#pragma warning disable CS1591 // Missing XML comment for publicly visible type or member
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

using global::Connectors.AI.SourceGraph;
using Models;


public interface ISourceGraphQLClient
{
    /// <summary>
    ///  Gets the repository id for the given repository name.
    /// </summary>
    /// <param name="repoName"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<string?> GetRepoIdAsync(string repoName, CancellationToken cancellationToken);


    /// <summary>
    ///  Gets the repository ids for the given repository names.
    /// </summary>
    /// <param name="repoNames"></param>
    /// <param name="count"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    IAsyncEnumerable<string>? GetRepoIds(IEnumerable<string> repoNames, int count, CancellationToken cancellationToken = default);


    /// <summary>
    ///  Gets the first <paramref name="count"/> repository names in the repository list of the  current context. 
    /// </summary>
    /// <param name="count"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<IEnumerable<string>?> GetRepoNamesAsync(int count, CancellationToken cancellationToken = default);


    /// <summary>
    /// Gets the repository for the given repository id. 
    /// </summary>
    /// <param name="repoName"> the repository name which is the url of the repository without the https prefix. i.e. github.com/microsoft/semantic-kernel</param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<Repository?> GetRepositoryAsync(string repoName, CancellationToken cancellationToken = default);


    /// <summary>
    ///  Checks if embedding exists for the given repository id.
    /// </summary>
    /// <param name="repoName"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<bool> GetRepositoryEmbeddingExistsAsync(string repoName, CancellationToken cancellationToken = default);


    /// <summary>
    ///  Determines whether the given query requires further context before it can be answered.
    /// For example: - "What is SKContext class in the SemanticKernel library" requires additional information from the Semantic-Kernel repository
    /// </summary>
    /// <param name="query"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<bool> IsContextRequiredAsync(string query, CancellationToken cancellationToken = default);


    /// <summary>
    ///  Gets a list of files in the given directory of the given repository id. 
    /// </summary>
    /// <param name="repoName"></param>
    /// <param name="branchName"></param>
    /// <param name="directory"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    IAsyncEnumerable<FileElement> GetRepositoryListOfFilesAsync(string repoName, string branchName = "main", string directory = "src", CancellationToken cancellationToken = default);


    /// <summary>
    /// Gets the content of the given file in the given repository id.
    /// </summary>
    /// <param name="repoName"></param>
    /// <param name="filePath"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<string?> GetRepositoryFileContentAsync(string repoName, string filePath, CancellationToken cancellationToken = default);


    /// <summary>
    /// Gets a list of references for the given symbol name in the given repository name.
    /// </summary>
    /// <param name="repoName"></param>
    /// <param name="symbolName"></param>
    /// <param name="includeContent"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    IAsyncEnumerable<Node?> GetSymbolReferencesAsync(string repoName, string symbolName, bool includeContent, CancellationToken cancellationToken = default);


    /// <summary>
    ///  Gets the code context for the given query in the given repositories.
    /// </summary>
    /// <param name="repos"></param>
    /// <param name="query"></param>
    /// <param name="codeResultsCount"></param>
    /// <param name="textResultsCount"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    IAsyncEnumerable<CodeContext>? GetCodeContextAsync(IEnumerable<string> repos, string query, int codeResultsCount, int textResultsCount, CancellationToken cancellationToken = default);


    /// <summary>
    ///  Gets the snippet attribution for the given snippet.
    /// </summary>
    /// <param name="snippet"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<SnippetAttribution?> GetSnippetAttributionAsync(string snippet, CancellationToken cancellationToken = default);
}
