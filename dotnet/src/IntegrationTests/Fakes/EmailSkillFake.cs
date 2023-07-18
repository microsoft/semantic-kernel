// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.SkillDefinition;

namespace SemanticKernel.IntegrationTests.Fakes;

internal sealed class EmailSkillFake
{
    [SKFunction, Description("Given an email address and message body, send an email")]
    public Task<string> SendEmailAsync(
        [Description("The body of the email message to send.")] string input,
        [Description("The email address to send email to.")] string? email_address = "default@email.com")
    {
        email_address ??= string.Empty;
        return Task.FromResult($"Sent email to: {email_address}. Body: {input}");
    }

    [SKFunction, Description("Lookup an email address for a person given a name")]
    public Task<string> GetEmailAddressAsync(
        [Description("The name of the person to email.")] string input,
        ILogger logger)
    {
        if (string.IsNullOrEmpty(input))
        {
            logger.LogTrace("Returning hard coded email for {0}", input);
            return Task.FromResult("johndoe1234@example.com");
        }

        logger.LogTrace("Returning dynamic email for {0}", input);
        return Task.FromResult($"{input}@example.com");
    }

    [SKFunction, Description("Write a short poem for an e-mail")]
    public Task<string> WritePoemAsync(
        [Description("The topic of the poem.")] string input)
    {
        return Task.FromResult($"Roses are red, violets are blue, {input} is hard, so is this test.");
    }
}
