﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates the creation of a new CRM entry
/// </summary>
public class CRMRecordCreationStep : KernelProcessStep
{
    public static class Functions
    {
        public const string CreateCRMEntry = nameof(CreateCRMEntry);
    }

    [KernelFunction(Functions.CreateCRMEntry)]
    public async Task CreateCRMEntryAsync(KernelProcessStepContext context, AccountUserInteractionDetails userInteractionDetails, Kernel _kernel)
    {
        // Placeholder for a call to API to create new CRM entry
        await context.EmitEventAsync(new() { Id = AccountOpeningEvents.CRMRecordInfoEntryCreated, Data = true });
    }
}
