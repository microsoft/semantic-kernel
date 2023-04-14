// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Graph;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.MsGraph.Diagnostics;

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
        /// The name of the select parameter used to select the properties to retrieve in the response.
        /// </summary>
        public const string Select = "select";

        /// <summary>
        /// The name of the filter parameter used to filter the results based on specific criteria.
        /// </summary>
        public const string Filter = "filter";

        /// <summary>
        /// The name of the top parameter used to limit the number of results returned in the response.
        /// </summary>
        public const string Top = "top";

        /// <summary>
        /// The name of the skip parameter used to skip a certain number of results in the response.
        /// </summary>
        public const string Skip = "skip";

        /// <summary>
        /// The name of the orderby parameter used to sort the results based on specific properties in either ascending or descending order.
        /// </summary>
        public const string OrderBy = "orderby";
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
        => await this._connector.GetMyEmailAddressAsync();

    /// <summary>
    /// Send an email using <see cref="ContextVariables.Input"/> as the body.
    /// </summary>
    [SKFunction("Send an email to one or more recipients.")]
    [SKFunctionInput(Description = "Email content/body")]
    [SKFunctionContextParameter(Name = Parameters.Recipients, Description = "Recipients of the email, separated by ',' or ';'.")]
    [SKFunctionContextParameter(Name = Parameters.Subject, Description = "Subject of the email")]
    public async Task SendEmailAsync(string content, SKContext context)
    {
        if (!context.Variables.Get(Parameters.Recipients, out string recipients))
        {
            context.Fail($"Missing variable {Parameters.Recipients}.");
            return;
        }

        if (!context.Variables.Get(Parameters.Subject, out string subject))
        {
            context.Fail($"Missing variable {Parameters.Subject}.");
            return;
        }

        this._logger.LogInformation("Sending email to '{0}' with subject '{1}'", recipients, subject);
        string[] recipientList = recipients.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
        await this._connector.SendEmailAsync(subject, content, recipientList);
    }

    /// <summary>
    /// Get email messages as the body
    /// </summary>
    [SKFunction("Get email messages with specified optional clauses used to query messages in Microsoft Graph")]
    [SKFunctionContextParameter(Name = Parameters.Select, Description = "The select parameter used to select the properties to retrieve in the response.")]
    [SKFunctionContextParameter(Name = Parameters.Filter, Description = "The filter parameter used to filter the results based on specific criteria.")]
    [SKFunctionContextParameter(Name = Parameters.Top, Description = "The top parameter used to limit the number of results returned in the response.")]
    [SKFunctionContextParameter(Name = Parameters.Skip, Description = "The skip parameter used to skip a certain number of results in the response.")]
    [SKFunctionContextParameter(Name = Parameters.OrderBy, Description = "The orderby parameter used to sort the results based on specific properties in either ascending or descending order.")]
    public async Task<string> GetEmailMessagesAsync(SKContext context)
    {
        this._logger.LogInformation("Getting email messages with query options select: '{0}', filter: '{1}', top: '{2}', skip:'{3}', orderby: '{4}'",
            context.Variables.Get(Parameters.Select, out string select),
            context.Variables.Get(Parameters.Filter, out string filter),
            context.Variables.Get(Parameters.Top, out string top),
            context.Variables.Get(Parameters.Skip, out string skip),
            context.Variables.Get(Parameters.OrderBy, out string orderBy)
        );

        IUserMessagesCollectionPage emailsPage = await this._connector.GetMessagesAsync(
            topClause: string.IsNullOrWhiteSpace(top) ? null : int.Parse(top),
            skipClause: string.IsNullOrWhiteSpace(skip) ? null : int.Parse(skip),
            filterClause: filter,
            orderByClause: orderBy,
            selectClause: select
        );

        // Serialize all email content either by their body or subject returned by the page and return as a string as skill output
        return string.Join('\0', emailsPage.Cast<Message>().ToList().Select(e => e.Body != null ? e.Body.Content : e.Subject).ToList());
    }
}
