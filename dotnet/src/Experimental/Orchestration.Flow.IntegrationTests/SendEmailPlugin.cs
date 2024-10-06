// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using Microsoft.SemanticKernel;
<<<<<<< HEAD
=======
using Microsoft.SemanticKernel.Orchestration;
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624

namespace SemanticKernel.Experimental.Orchestration.Flow.IntegrationTests;

public sealed class SendEmailPlugin
{
<<<<<<< HEAD
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
=======
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
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
            Content = answer,
        };

        // for demo purpose only
<<<<<<< HEAD
        string emailPayload = JsonSerializer.Serialize(contract, s_writeIndented);
        variables["email"] = emailPayload;
=======
        string emailPayload = JsonSerializer.Serialize(contract, new JsonSerializerOptions() { WriteIndented = true });
        context.Variables["email"] = emailPayload;
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624

        return "Here's the API contract I will post to mail server: " + emailPayload;
    }

    private sealed class Email
    {
        public string? Address { get; set; }

        public string? Content { get; set; }
    }
}
