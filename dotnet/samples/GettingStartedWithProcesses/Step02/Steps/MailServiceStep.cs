// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates Mail Service with a message for the user.
/// </summary>
public class MailServiceStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string SendMailToUserWithDetails = nameof(SendMailToUserWithDetails);
    }

    [KernelFunction(ProcessStepFunctions.SendMailToUserWithDetails)]
    public async Task SendMailServiceAsync(KernelProcessStepContext context, string message)
    {
        Console.WriteLine("======== MAIL SERVICE ======== ");
        Console.WriteLine(message);
        Console.WriteLine("============================== ");

        await context.EmitEventAsync(new() { Id = AccountOpeningEvents.MailServiceSent, Data = message });
    }
}
