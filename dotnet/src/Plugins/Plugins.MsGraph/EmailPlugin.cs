// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Plugins.MsGraph.Diagnostics;
using Microsoft.SemanticKernel.Plugins.MsGraph.Models;

namespace Microsoft.SemanticKernel.Plugins.MsGraph;

/// <summary>
/// Email plugin (e.g. Outlook).
/// </summary>
public sealed class EmailPlugin
{
    private readonly IEmailConnector _connector;
    private readonly ILogger _logger;
    private static readonly JsonSerializerOptions s_options = new()
    {
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };
    private static readonly char[] s_separator = [',', ';'];

    /// <summary>
    /// Initializes a new instance of the <see cref="EmailPlugin"/> class.
    /// </summary>
    /// <param name="connector">Email connector.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public EmailPlugin(IEmailConnector connector, ILoggerFactory? loggerFactory = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._connector = connector;
        this._logger = loggerFactory?.CreateLogger(typeof(EmailPlugin)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Get my email address.
    /// </summary>
    [KernelFunction, Description("Gets the email address for me.")]
    public async Task<string?> GetMyEmailAddressAsync()
        => await this._connector.GetMyEmailAddressAsync().ConfigureAwait(false);

    /// <summary>
    /// Send an email.
    /// </summary>
    [KernelFunction, Description("Send an email to one or more recipients.")]
    public async Task SendEmailAsync(
        [Description("Email content/body")] string content,
        [Description("Recipients of the email, separated by ',' or ';'.")] string recipients,
        [Description("Subject of the email")] string subject,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(recipients))
        {
            throw new ArgumentException("Variable was null or whitespace", nameof(recipients));
        }

        if (string.IsNullOrWhiteSpace(subject))
        {
            throw new ArgumentException("Variable was null or whitespace", nameof(subject));
        }

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Sending email to '{0}' with subject '{1}'", recipients, subject);
        string[] recipientList = recipients.Split(s_separator, StringSplitOptions.RemoveEmptyEntries);
        await this._connector.SendEmailAsync(subject, content, recipientList, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Get email messages with specified optional clauses used to query for messages.
    /// </summary>
    [KernelFunction, Description("Get email messages.")]
    public async Task<string?> GetEmailMessagesAsync(
        [Description("Optional limit of the number of message to retrieve.")] int? maxResults = 10,
        [Description("Optional number of message to skip before retrieving results.")] int? skip = 0,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting email messages with query options top: '{0}', skip:'{1}'.", maxResults, skip);

        const string SelectString = "subject,receivedDateTime,bodyPreview";

        IEnumerable<EmailMessage>? messages = await this._connector.GetMessagesAsync(
                top: maxResults,
                skip: skip,
                select: SelectString,
                cancellationToken)
            .ConfigureAwait(false);

        if (messages is null)
        {
            return null;
        }

        return JsonSerializer.Serialize(value: messages, options: s_options);
    }
}
