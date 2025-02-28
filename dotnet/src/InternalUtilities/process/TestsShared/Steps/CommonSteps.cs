// Copyright (c) Microsoft. All rights reserved.
using System.Threading;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.TestsShared.Steps;

/// <summary>
/// Collection of common steps used by UnitTests and IntegrationUnitTests
/// </summary>
public static class CommonSteps
{
    /// <summary>
    /// The step that counts how many times it has been invoked.
    /// </summary>
    public sealed class CountStep : KernelProcessStep
    {
        public const string CountFunction = nameof(Count);

        public static int Index = 0;

        [KernelFunction]
        public string Count()
        {
            Interlocked.Increment(ref Index);
            return Index.ToString();
        }
    }
}
