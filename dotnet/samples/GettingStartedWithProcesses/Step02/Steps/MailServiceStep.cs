// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates Mail Service with a message for the user.
/// </summary>
public class MailServiceStep : KernelProcessStep<MailServiceState>
{
    public static class Functions
    {
        public const string SendMailToUserWithDetails = nameof(SendMailToUserWithDetails);
    }

    private MailServiceState? _state;

    public override ValueTask ActivateAsync(KernelProcessStepState<MailServiceState> state)
    {
        this._state = state.State;
        return default;
    }

    [KernelFunction(Functions.SendMailToUserWithDetails)]
    public async Task SendMailServiceAsync(KernelProcessStepContext context, string message)
    {
        this._state!.LastMessageSent = message;
        Console.WriteLine("======== MAIL SERVICE ======== ");
        Console.WriteLine(message);
        Console.WriteLine("============================== ");

        await context.EmitEventAsync(new() { Id = AccountOpeningEvents.MailServiceSent, Data = message });
    }
}

public class MailServiceState
{
    public string? LastMessageSent = null;
}
