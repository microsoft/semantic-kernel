// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Graph.Me.SendMail;
using Microsoft.Graph.Models;

namespace ProcessWithCloudEvents.MicrosoftGraph;

public static class GraphRequestFactory
{
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
