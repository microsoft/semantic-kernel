// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.Graph.Models;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.Diagnostics;
using Microsoft.SemanticKernel.Plugins.MsGraph.Models;

namespace Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;

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
    public async Task<string?> GetMyEmailAddressAsync(CancellationToken cancellationToken = default)
        => (await this._graphServiceClient.Me.GetAsync(cancellationToken: cancellationToken).ConfigureAwait(false))?.UserPrincipalName;

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
            }).ToList()
        };

        await this._graphServiceClient.Me.SendMail.PostAsync(new() { Message = message }, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<Models.EmailMessage>?> GetMessagesAsync(
        int? top, int? skip, string? select, CancellationToken cancellationToken = default)
    {
        var result = await this._graphServiceClient.Me.Messages.GetAsync((config) =>
        {
            config.QueryParameters.Top = top;
            config.QueryParameters.Skip = skip;
            config.QueryParameters.Select = !string.IsNullOrEmpty(select) ? [select] : null;
        }, cancellationToken: cancellationToken).ConfigureAwait(false);

        IEnumerable<EmailMessage>? messages = result?.Value?.Select(m => m.ToEmailMessage());

        return messages;
    }
}
