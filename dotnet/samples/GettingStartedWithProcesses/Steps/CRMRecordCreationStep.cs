// Copyright (c) Microsoft. All rights reserved.

using Events;
using Microsoft.SemanticKernel;
using Models;

namespace Steps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_02_AccountOpening.cs
/// </summary>
public class CRMRecordCreationStep : KernelProcessStep
{
    public static class Functions
    {
        public const string CreateCRMEntry = "CreateCRMEntry";
    }

    [KernelFunction(Functions.CreateCRMEntry)]
    public async Task CreateCRMEntryAsync(KernelProcessStepContext context, AccountUserInteractionDetails userInteractionDetails, Kernel _kernel)
    {
        // Placeholder for a call to API to create new CRM entry
        await context.EmitEventAsync(new() { Id = AccountOpeningEvents.CRMRecordInfoEntryCreated, Data = true });
    }
}
