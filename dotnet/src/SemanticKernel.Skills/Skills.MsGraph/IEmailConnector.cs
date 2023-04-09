// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Interface for email connections (e.g. Outlook).
/// </summary>
public interface IEmailConnector
{
    /// <summary>
    /// Get the user's email address.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The user's email address.</returns>
    Task<string> GetMyEmailAddressAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Send an email to the specified recipients.
    /// </summary>
    /// <param name="subject">Email subject.</param>
    /// <param name="content">Email content.</param>
    /// <param name="recipients">Email recipients.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task SendEmailAsync(string subject, string content, string[] recipients, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get the user's messages.
    /// </summary>
    /// <param name="topClause">Top Clause</param>
    /// <param name="skipClause">Skip Clause</param>
    /// <param name="filterClause">Filter Clause</param>
    /// <param name="orderByClause">OrderBy Clause</param>
    /// <param name="selectClause">Select Clause</param>
    /// <returns></returns>
    Task<IUserMessagesCollectionPage> GetMessagesAsync(int? topClause = 100, int? skipClause = null, string? filterClause = null, string? orderByClause = null, string? selectClause = null);
}
