// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.IntegrationTests.Fakes;

internal sealed class EmailSkillFake
{
    [SKFunction("Given an email address and message body, send an email")]
    [SKFunctionInput(Description = "The body of the email message to send.")]
    [SKFunctionContextParameter(Name = "email_address", Description = "The email address to send email to.", DefaultValue = "default@email.com")]
    public Task<SKContext> SendEmailAsync(string input, SKContext context)
    {
        context.Variables.TryGetValue("email_address", out string? emailAddress);
        context.Variables.Update($"Sent email to: {emailAddress}. Body: {input}");
        return Task.FromResult(context);
    }

    [SKFunction("Lookup an email address for a person given a name")]
    [SKFunctionInput(Description = "The name of the person to email.")]
    public Task<SKContext> GetEmailAddressAsync(string input, SKContext context)
    {
        if (string.IsNullOrEmpty(input))
        {
            context.Log.LogDebug("Returning hard coded email for {0}", input);
            context.Variables.Update("johndoe1234@example.com");
        }
        else
        {
            context.Log.LogDebug("Returning dynamic email for {0}", input);
            context.Variables.Update($"{input}@example.com");
        }

        return Task.FromResult(context);
    }

    [SKFunction("Write a short poem for an e-mail")]
    [SKFunctionInput(Description = "The topic of the poem.")]
    public Task<SKContext> WritePoemAsync(string input, SKContext context)
    {
        context.Variables.Update($"Roses are red, violets are blue, {input} is hard, so is this test.");
        return Task.FromResult(context);
    }
}
