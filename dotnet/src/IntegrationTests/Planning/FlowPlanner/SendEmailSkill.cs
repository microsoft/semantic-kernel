// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.Planning.FlowPlanner;

using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using System.ComponentModel;
using System.Text.Json;

public sealed class SendEmailSkill
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
