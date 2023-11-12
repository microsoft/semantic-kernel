// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents an execution run on a thread.
/// </summary>
internal interface IChatRun
{
    /// <summary>
    /// The run identifier (which can be referenced in API endpoints).
    /// </summary>
    string Id { get; }

    /// <summary>
    /// The assistant identifier (which can be referenced in API endpoints).
    /// </summary>
    string AssistantId { get; }

    /// <summary>
    /// The thread identifier (which can be referenced in API endpoints).
    /// </summary>
    string ThreadId { get; }

    /// <summary>
    /// Retrieve and process the result of the run, includes polling and tool processing.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>$$$ TBD</returns>
    Task<IList<string>> GetResultAsync(CancellationToken cancellationToken = default);
}
