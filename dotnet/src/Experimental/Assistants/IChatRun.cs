// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// $$$
/// </summary>
internal interface IChatRun
{
    /// <summary>
    /// $$$
    /// </summary>
    string Id { get; }

    /// <summary>
    /// $$$
    /// </summary>
    string AssistantId { get; }

    /// <summary>
    /// $$$
    /// </summary>
    string ThreadId { get; }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task<string> GetResultAsync(CancellationToken cancellationToken = default);
}
