﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates the creation a new marketing user entry.
/// </summary>
public class NewMarketingEntryStep : KernelProcessStep
{
    public static class Functions
    {
        public const string CreateNewMarketingEntry = nameof(CreateNewMarketingEntry);
    }

    [KernelFunction(Functions.CreateNewMarketingEntry)]
    public async Task CreateNewMarketingEntryAsync(KernelProcessStepContext context, MarketingNewEntryDetails userDetails, Kernel _kernel)
    {
        // Placeholder for a call to API to create new entry of user for marketing purposes
        await context.EmitEventAsync(new() { Id = AccountOpeningEvents.NewMarketingEntryCreated, Data = true });
    }
}
