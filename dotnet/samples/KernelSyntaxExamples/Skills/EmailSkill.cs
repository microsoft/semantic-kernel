// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Skills;

internal sealed class EmailSkill
{
    [SKFunction, Description("Given an e-mail and message body, send an email")]
    public string SendEmail(
        [Description("The body of the email message to send.")] string input,
        [Description("The email address to send email to.")] string email_address) =>

        $"Sent email to: {email_address}. Body: {input}";

    [SKFunction, Description("Given a name, find email address")]
    public string GetEmailAddress(
        [Description("The name of the person whose email address needs to be found.")] string input,
        ILogger? logger = null)
    {
        // Sensitive data, logging as trace, disabled by default
        logger?.LogTrace("Returning hard coded email for {0}", input);

        return "johndoe1234@example.com";
    }
}
