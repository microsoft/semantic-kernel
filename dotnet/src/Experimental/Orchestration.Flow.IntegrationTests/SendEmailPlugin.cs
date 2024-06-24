// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Experimental.Orchestration.Flow.IntegrationTests;

public sealed class SendEmailPlugin
{
    private static readonly JsonSerializerOptions s_writeIndented = new() { WriteIndented = true };

    [KernelFunction]
    [Description("Send email")]
    public string SendEmail(
        // ReSharper disable once InconsistentNaming
#pragma warning disable CA1707 // Identifiers should not contain underscores
        string email_address,
#pragma warning restore CA1707 // Identifiers should not contain underscores
        string answer,
        KernelArguments variables)
    {
        var contract = new Email()
        {
            Address = email_address,
            Content = answer,
        };

        // for demo purpose only
        string emailPayload = JsonSerializer.Serialize(contract, s_writeIndented);
        variables["email"] = emailPayload;

        return "Here's the API contract I will post to mail server: " + emailPayload;
    }

    private sealed class Email
    {
        public string? Address { get; set; }

        public string? Content { get; set; }
    }
}
