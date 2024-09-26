// Copyright (c) Microsoft. All rights reserved.

using Events;
using Microsoft.SemanticKernel;
using Models;

namespace Steps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_02_AccountOpening.cs
/// </summary>
public class NewMarketingEntryStep : KernelProcessStep
{
    public static class Functions
    {
        public const string CreateNewMarketingEntry = "CreateNewMarketingEntry";
    }

    [KernelFunction(Functions.CreateNewMarketingEntry)]
    public async Task CreateNewMarketingEntryAsync(KernelProcessStepContext context, MarketingNewEntryDetails userDetails, Kernel _kernel)
    {
        // Placeholder for a call to API to create new entry of user for marketing purposes
        await context.EmitEventAsync(new() { Id = AccountOpeningEvents.NewMarketingEntryCreated, Data = true });
    }
}
