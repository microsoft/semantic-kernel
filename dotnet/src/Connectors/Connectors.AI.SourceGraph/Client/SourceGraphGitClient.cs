// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

using Extensions;
using global::Connectors.AI.SourceGraph;
using StrawberryShake;


public class SourceGraphGitClient : ISourceGraphGitClient
{
    private readonly ISourceGraphClient _sourceGraphClient;

    public SourceGraphGitClient(ISourceGraphClient sourceGraphClient) => _sourceGraphClient = sourceGraphClient;


    /// <inheritdoc />
    public async Task<Comparison> GitDiffAsync(string repoName, string baseRef, string headRef, CancellationToken cancellationToken = default)
    {
        IOperationResult<IGitDiffQueryResult> queryResponse = await _sourceGraphClient.GitDiffQuery.ExecuteAsync(repoName, baseRef, headRef, cancellationToken).ConfigureAwait(false);
        queryResponse.EnsureNoErrors();
        var response = queryResponse.ToSourceGraphResponse();
        return response.Data.Repository.Comparison;
    }
}
