// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.TestsShared.Steps;

#pragma warning disable CS1591 // Missing XML comment for publicly visible type or member

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

#pragma warning disable CA2211
        // workaround for unit testing evaluation purposes
        public static int Index = 0;
#pragma warning restore CA2211
        [KernelFunction]
        public string Count()
        {
            Interlocked.Increment(ref Index);
            return Index.ToString();
        }
    }

    /// <summary>
    /// The step that counts how many times it has been invoked.
    /// </summary>
    public sealed class EvenNumberDetectorStep : KernelProcessStep
    {
        /// <summary>
        /// Output events emitted by <see cref="EvenNumberDetectorStep"/>
        /// </summary>
        public static class OutputEvents
        {
            /// <summary>
            /// Event number event name
            /// </summary>
            public const string EvenNumber = nameof(EvenNumber);
            /// <summary>
            /// Event number event name
            /// </summary>
            public const string OddNumber = nameof(OddNumber);
        }

        /// <summary>
        /// Step that emits different event depending if the number is odd or even
        /// </summary>
        /// <param name="numberString">number to be evaluated</param>
        /// <param name="context">instance of <see cref="KernelProcessStepContext"/></param>
        /// <returns></returns>
        [KernelFunction]
        public async Task DetectEvenNumberAsync(string numberString, KernelProcessStepContext context)
        {
            var number = int.Parse(numberString);
            if (number % 2 == 0)
            {
                await context.EmitEventAsync(OutputEvents.EvenNumber, numberString);
                return;
            }

            await context.EmitEventAsync(OutputEvents.OddNumber, numberString);
        }
    }

    /// <summary>
    /// A step that echos its input.
    /// </summary>
    public sealed class EchoStep : KernelProcessStep
    {
        [KernelFunction]
        public string Echo(string message)
        {
            Console.WriteLine($"[ECHO] {message}");
            return message;
        }
    }

#pragma warning restore CS1591 // Missing XML comment for publicly visible type or member

}
