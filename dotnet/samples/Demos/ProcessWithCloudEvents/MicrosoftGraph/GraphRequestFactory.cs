// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Graph.Me.SendMail;
using Microsoft.Graph.Models;

namespace ProcessWithCloudEvents.MicrosoftGraph;

/// <summary>
/// Factory that creates Microsoft Graph related objects
/// </summary>
public static class GraphRequestFactory
{
    /// <summary>
    /// Method that creates MailPost Body with defined subject, content and recipients
    /// </summary>
    /// <param name="subject">subject of the email</param>
    /// <param name="content">content of the email</param>
    /// <param name="recipients">recipients of the email</param>
    /// <returns><see cref="SendMailPostRequestBody"/></returns>
    public static SendMailPostRequestBody CreateEmailBody(string subject, string content, List<string> recipients)
    {
        var message = new SendMailPostRequestBody()
        {
            Message = new Microsoft.Graph.Models.Message()
            {
                Subject = subject,
                Body = new()
                {
                    ContentType = Microsoft.Graph.Models.BodyType.Text,
                    Content = content,
                },
                ToRecipients = recipients.Select(address => new Recipient { EmailAddress = new() { Address = address } }).ToList(),
            },
            SaveToSentItems = true,
        };

        return message;
    }
}
