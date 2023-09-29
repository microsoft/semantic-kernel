// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;

namespace SemanticKernel.IntegrationTests.Orchestration.Flow;

public sealed class SendEmailPlugin
{
    [SKFunction]
    [Description("Send email")]
    [SKName("SendEmail")]
    public string SendEmail(
        [SKName("email_address")] string emailAddress,
        [SKName("answer")] string answer,
        SKContext context)
    {
        var contract = new Email()
        {
            Address = emailAddress,
            Content = answer,
        };

        // for demo purpose only
        string emailPayload = JsonSerializer.Serialize(contract, new JsonSerializerOptions() { WriteIndented = true });
        context.Variables["email"] = emailPayload;

        return "Here's the API contract I will post to mail server: " + emailPayload;
    }

    private sealed class Email
    {
        public string? Address { get; set; }

        public string? Content { get; set; }
    }
}
