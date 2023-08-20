// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

using global::Connectors.AI.SourceGraph;


public interface ISourceGraphGitClient
{

    /// <summary>
    ///  Gets a comparison between two refs in a repository.
    /// </summary>
    /// <param name="repoName"></param>
    /// <param name="baseRef"></param>
    /// <param name="headRef"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<Comparison> GitDiffAsync(string repoName, string baseRef, string headRef, CancellationToken cancellationToken = default);
}
