﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates a Fraud detection check, based on the userId the fraud detection will pass or fail.
/// </summary>
public class FraudDetectionStep : KernelProcessStep
{
    public static class Functions
    {
        public const string FraudDetectionCheck = nameof(FraudDetectionCheck);
    }

    [KernelFunction(Functions.FraudDetectionCheck)]
    public async Task FraudDetectionCheckAsync(KernelProcessStepContext context, bool previousCheckSucceeded, NewCustomerForm customerDetails, Kernel _kernel)
    {
        // Placeholder for a call to API to validate user details for fraud detection
        if (customerDetails.UserId == "123-456-7890")
        {
            await context.EmitEventAsync(new()
            {
                Id = AccountOpeningEvents.FraudDetectionCheckFailed,
                Data = "We regret to inform you that we found some inconsistent details regarding the information you provided regarding the new account of the type PRIME ABC you applied."
            });
            return;
        }

        await context.EmitEventAsync(new() { Id = AccountOpeningEvents.FraudDetectionCheckPassed, Data = true });
    }
}
