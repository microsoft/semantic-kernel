// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable IDE0130

namespace ExampleSkills;

internal sealed class EmailSkill
{
    [SKFunction("Given an e-mail and message body, send an email")]
    [SKFunctionInput(Description = "The body of the email message to send.")]
    [SKFunctionContextParameter(Name = "email_address", Description = "The email address to send email to.")]
    public Task<SKContext> SendEmail(string input, SKContext context)
    {
        context.Variables.Update($"Sent email to: {context.Variables["email_address"]}. Body: {input}");
        return Task.FromResult(context);
    }

    [SKFunction("Given a name, find email address")]
    [SKFunctionInput(Description = "The name of the person to email.")]
    public Task<SKContext> GetEmailAddress(string input, SKContext context)
    {
        context.Log.LogDebug("Returning hard coded email for {0}", input);
        context.Variables.Update("johndoe1234@example.com");
        return Task.FromResult(context);
    }
}
