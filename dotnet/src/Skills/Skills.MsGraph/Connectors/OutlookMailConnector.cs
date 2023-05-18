// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.SemanticKernel.Skills.MsGraph.Connectors.Diagnostics;
using Microsoft.SemanticKernel.Skills.MsGraph.Models;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Connectors;

/// <summary>
/// Connector for Outlook Mail API
/// </summary>
public class OutlookMailConnector : IEmailConnector
{
    private readonly GraphServiceClient _graphServiceClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="OutlookMailConnector"/> class.
    /// </summary>
    /// <param name="graphServiceClient">A graph service client.</param>
    public OutlookMailConnector(GraphServiceClient graphServiceClient)
    {
        this._graphServiceClient = graphServiceClient;
    }

    /// <inheritdoc/>
    public async Task<string> GetMyEmailAddressAsync(CancellationToken cancellationToken = default)
        => (await this._graphServiceClient.Me.Request().GetAsync(cancellationToken).ConfigureAwait(false)).UserPrincipalName;

    /// <inheritdoc/>
    public async Task SendEmailAsync(string subject, string content, string[] recipients, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(subject, nameof(subject));
        Ensure.NotNullOrWhitespace(content, nameof(content));
        Ensure.NotNull(recipients, nameof(recipients));

        Message message = new()
        {
            Subject = subject,
            Body = new ItemBody { ContentType = BodyType.Text, Content = content },
            ToRecipients = recipients.Select(recipientAddress => new Recipient
            {
                EmailAddress = new()
                {
                    Address = recipientAddress
                }
            })
        };

        await this._graphServiceClient.Me.SendMail(message).Request().PostAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<Models.EmailMessage>> GetMessagesAsync(
        int? top, int? skip, string? select, CancellationToken cancellationToken = default)
    {
        IUserMessagesCollectionRequest query = this._graphServiceClient.Me.Messages.Request();

        if (top.HasValue)
        {
            query.Top(top.Value);
        }

        if (skip.HasValue)
        {
            query.Skip(skip.Value);
        }

        if (!string.IsNullOrEmpty(select))
        {
            query.Select(select);
        }

        IUserMessagesCollectionPage result = await query.GetAsync(cancellationToken).ConfigureAwait(false);

        IEnumerable<EmailMessage> messages = result.Select(m => m.ToEmailMessage());

        return messages;
    }
}
