// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using SemanticKernel.Process.TestsShared.Services;

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
    public sealed class CountStep : KernelProcessStep<CounterState>
    {
        public const string CountFunction = nameof(Count);

        private readonly ICounterService _counter;

        private CounterState? _state;
        public CountStep(ICounterService counterService)
        {
            this._counter = counterService;
        }

        public override ValueTask ActivateAsync(KernelProcessStepState<CounterState> state)
        {
            this._state = state.State ?? new();
            this._counter.SetCount(this._state.Count);
            Console.WriteLine($"Activating counter with value {this._state.Count}");
            return base.ActivateAsync(state);
        }

        [KernelFunction]
        public string Count()
        {
            int count = this._counter.IncreaseCount();
            this._state!.Count = count;
            return count.ToString();
        }
    }

    public class CounterState
    {
        public int Count { get; set; } = 0;
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

    /// <summary>
    /// A step that echos its input. Delays input for a specified amount of time.
    /// </summary>
    public sealed class DelayedEchoStep : KernelProcessStep
    {
        public static class OutputEvents
        {
            public const string DelayedEcho = nameof(DelayedEcho);
        }

        private readonly int _delayInMs = 1000;

        [KernelFunction]
        public async Task<string> EchoAsync(KernelProcessStepContext context, string message)
        {
            // Simulate a delay
            Thread.Sleep(this._delayInMs);
            Console.WriteLine($"[DELAYED_ECHO-{this.StepName}]: {message}");
            await context.EmitEventAsync(OutputEvents.DelayedEcho, data: message);
            return message;
        }
    }

    public sealed class MergeStringsStep : KernelProcessStep
    {
        [KernelFunction]
        public IList<string> MergeStrings(string str1, string str2, string str3)
        {
            Console.WriteLine($"[MERGE_STRINGS-{this.StepName}] {str1} {str2} {str3}");
            return [str1, str2, str3];
        }
    }
}
