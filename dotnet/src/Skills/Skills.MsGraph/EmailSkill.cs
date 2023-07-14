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
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.MsGraph.Diagnostics;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Email skill (e.g. Outlook).
/// </summary>
public sealed class EmailSkill
{
    /// <summary>
    /// <see cref="ContextVariables"/> parameter names.
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// Email recipients, separated by ',' or ';'.
        /// </summary>
        public const string Recipients = "recipients";

        /// <summary>
        /// Email subject.
        /// </summary>
        public const string Subject = "subject";

        /// <summary>
        /// The name of the top parameter used to limit the number of results returned in the response.
        /// </summary>
        public const string MaxResults = "maxResults";

        /// <summary>
        /// The name of the skip parameter used to skip a certain number of results in the response.
        /// </summary>
        public const string Skip = "skip";
    }

    private readonly IEmailConnector _connector;
    private readonly ILogger<EmailSkill> _logger;
    private static readonly JsonSerializerOptions s_options = new()
    {
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    /// <summary>
    /// Initializes a new instance of the <see cref="EmailSkill"/> class.
    /// </summary>
    /// <param name="connector">Email connector.</param>
    /// <param name="logger">Logger.</param>
    public EmailSkill(IEmailConnector connector, ILogger<EmailSkill>? logger = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._connector = connector;
        this._logger = logger ?? new NullLogger<EmailSkill>();
    }

    /// <summary>
    /// Get my email address.
    /// </summary>
    [SKFunction, Description("Gets the email address for me.")]
    public async Task<string> GetMyEmailAddressAsync()
        => await this._connector.GetMyEmailAddressAsync().ConfigureAwait(false);

    /// <summary>
    /// Send an email using <see cref="ContextVariables.Input"/> as the body.
    /// </summary>
    [SKFunction, Description("Send an email to one or more recipients.")]
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
        string[] recipientList = recipients.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
        await this._connector.SendEmailAsync(subject, content, recipientList, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Get email messages with specified optional clauses used to query for messages.
    /// </summary>
    [SKFunction, Description("Get email messages.")]
    public async Task<string> GetEmailMessagesAsync(
        [Description("Optional limit of the number of message to retrieve.")] int? maxResults = 10,
        [Description("Optional number of message to skip before retrieving results.")] int? skip = 0,
        CancellationToken cancellationToken = default)
    {
        this._logger.LogDebug("Getting email messages with query options top: '{0}', skip:'{1}'.", maxResults, skip);

        const string SelectString = "subject,receivedDateTime,bodyPreview";

        IEnumerable<EmailMessage> messages = await this._connector.GetMessagesAsync(
                top: maxResults,
                skip: skip,
                select: SelectString,
                cancellationToken)
            .ConfigureAwait(false);

        return JsonSerializer.Serialize(value: messages, options: s_options);
    }
}
