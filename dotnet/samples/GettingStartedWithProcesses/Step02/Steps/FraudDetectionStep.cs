// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step02.Models;

namespace Step02.Steps;

/// <summary>
/// Mock step that emulates a Fraud detection check, based on the userId the fraud detection will pass or fail.
/// </summary>
public class FraudDetectionStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string FraudDetectionCheck = nameof(FraudDetectionCheck);
    }

    [KernelFunction(ProcessStepFunctions.FraudDetectionCheck)]
    public async Task FraudDetectionCheckAsync(KernelProcessStepContext context, bool previousCheckSucceeded, NewCustomerForm customerDetails, Kernel _kernel)
    {
        // Placeholder for a call to API to validate user details for fraud detection
        if (customerDetails.UserId == "123-456-7890")
        {
            Console.WriteLine("[FRAUD CHECK] Fraud Check Failed");
            await context.EmitEventAsync(new()
            {
                Id = AccountOpeningEvents.FraudDetectionCheckFailed,
                Data = "We regret to inform you that we found some inconsistent details regarding the information you provided regarding the new account of the type PRIME ABC you applied.",
                Visibility = KernelProcessEventVisibility.Public,
            });
            return;
        }

        Console.WriteLine("[FRAUD CHECK] Fraud Check Passed");
        await context.EmitEventAsync(new() { Id = AccountOpeningEvents.FraudDetectionCheckPassed, Data = true, Visibility = KernelProcessEventVisibility.Public });
    }
}
