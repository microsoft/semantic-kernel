// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
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
public class EmailSkill
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
    [SKFunction("Gets the email address for me.")]
    public async Task<string> GetMyEmailAddressAsync()
        => await this._connector.GetMyEmailAddressAsync().ConfigureAwait(false);

    /// <summary>
    /// Send an email using <see cref="ContextVariables.Input"/> as the body.
    /// </summary>
    [SKFunction("Send an email to one or more recipients.")]
    [SKFunctionInput(Description = "Email content/body")]
    [SKFunctionContextParameter(Name = Parameters.Recipients, Description = "Recipients of the email, separated by ',' or ';'.")]
    [SKFunctionContextParameter(Name = Parameters.Subject, Description = "Subject of the email")]
    public async Task SendEmailAsync(string content, SKContext context)
    {
        if (!context.Variables.TryGetValue(Parameters.Recipients, out string? recipients))
        {
            context.Fail($"Missing variable {Parameters.Recipients}.");
            return;
        }

        if (!context.Variables.TryGetValue(Parameters.Subject, out string? subject))
        {
            context.Fail($"Missing variable {Parameters.Subject}.");
            return;
        }

        this._logger.LogInformation("Sending email to '{0}' with subject '{1}'", recipients, subject);
        string[] recipientList = recipients.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
        await this._connector.SendEmailAsync(subject, content, recipientList).ConfigureAwait(false);
    }

    /// <summary>
    /// Get email messages with specified optional clauses used to query for messages.
    /// </summary>
    [SKFunction("Get email messages.")]
    [SKFunctionContextParameter(Name = Parameters.MaxResults, Description = "Optional limit of the number of message to retrieve.",
        DefaultValue = "10")]
    [SKFunctionContextParameter(Name = Parameters.Skip, Description = "Optional number of message to skip before retrieving results.",
        DefaultValue = "0")]
    public async Task<string> GetEmailMessagesAsync(SKContext context)
    {
        context.Variables.TryGetValue(Parameters.MaxResults, out string? maxResultsString);
        context.Variables.TryGetValue(Parameters.Skip, out string? skipString);
        this._logger.LogInformation("Getting email messages with query options top: '{0}', skip:'{1}'.", maxResultsString, skipString);

        string selectString = "subject,receivedDateTime,bodyPreview";

        int? top = null;
        if (!string.IsNullOrWhiteSpace(maxResultsString))
        {
            if (int.TryParse(maxResultsString, out int topValue))
            {
                top = topValue;
            }
        }

        int? skip = null;
        if (!string.IsNullOrWhiteSpace(skipString))
        {
            if (int.TryParse(skipString, out int skipValue))
            {
                skip = skipValue;
            }
        }

        IEnumerable<EmailMessage> messages = await this._connector.GetMessagesAsync(
                top: top,
                skip: skip,
                select: selectString,
                context.CancellationToken)
            .ConfigureAwait(false);

        return JsonSerializer.Serialize(
            value: messages,
            options: new JsonSerializerOptions
            {
                WriteIndented = false,
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            });
    }
}
