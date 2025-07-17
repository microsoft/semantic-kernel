// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates the creation of a new CRM entry
/// </summary>
public class CRMRecordCreationStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string CreateCRMEntry = nameof(CreateCRMEntry);
    }

    [KernelFunction(ProcessStepFunctions.CreateCRMEntry)]
    public async Task CreateCRMEntryAsync(KernelProcessStepContext context, AccountUserInteractionDetails userInteractionDetails, Kernel _kernel)
    {
        Console.WriteLine($"[CRM ENTRY CREATION] New Account {userInteractionDetails.AccountId} created");

        // Placeholder for a call to API to create new CRM entry
        await context.EmitEventAsync(new() { Id = AccountOpeningEvents.CRMRecordInfoEntryCreated, Data = true });
    }
}
