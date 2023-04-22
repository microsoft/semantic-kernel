// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.SemanticKernel.Skills.MsGraph.Connectors.Diagnostics;

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
        => (await this._graphServiceClient.Me.Request().GetAsync(cancellationToken)).UserPrincipalName;

    /// <inheritdoc/>
    public async Task SendEmailAsync(string subject, string content, string[] recipients, CancellationToken cancellationToken = default)
    {
        Ensure.NotNullOrWhitespace(subject, nameof(subject));
        Ensure.NotNullOrWhitespace(content, nameof(content));
        Ensure.NotNull(recipients, nameof(recipients));

        Message message = new Message
        {
            Subject = subject,
            Body = new ItemBody { ContentType = BodyType.Text, Content = content },
            ToRecipients = recipients.Select(recipientAddress => new Recipient
            {
                EmailAddress = new EmailAddress
                {
                    Address = recipientAddress
                }
            })
        };

        await this._graphServiceClient.Me.SendMail(message).Request().PostAsync(cancellationToken);
    }
}
