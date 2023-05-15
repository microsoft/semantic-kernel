// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Interface for email connections (e.g. Outlook).
/// </summary>
public interface IEmailConnector
{
    /// <summary>
    /// Get the user's email address.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The user's email address.</returns>
    Task<string> GetMyEmailAddressAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Send an email to the specified recipients.
    /// </summary>
    /// <param name="subject">Email subject.</param>
    /// <param name="content">Email content.</param>
    /// <param name="recipients">Email recipients.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task SendEmailAsync(string subject, string content, string[] recipients, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get the user's email messages.
    /// </summary>
    /// <param name="top">How many messages to get.</param>
    /// <param name="skip">How many messages to skip.</param>
    /// <param name="select">Optionally select which message properties to get.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>The user's email messages.</returns>
#pragma warning disable CA1716 // Identifiers should not match keywords
    Task<IEnumerable<EmailMessage>> GetMessagesAsync(int? top, int? skip, string? @select, CancellationToken cancellationToken = default);
#pragma warning restore CA1716 // Identifiers should not match keywords
}
