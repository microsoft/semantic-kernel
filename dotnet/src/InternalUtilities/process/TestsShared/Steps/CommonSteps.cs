// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable IDE0005 // Using directive is unnecessary
using System;
using System.Threading;
using System.Threading.Tasks;
#pragma warning restore IDE0005 // Using directive is unnecessary
using Microsoft.SemanticKernel.Process.TestsShared.Services;

namespace Microsoft.SemanticKernel.Process.TestsShared.Steps;

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
    public sealed class SimpleCountStep : KernelProcessStep<CounterState>
    {
        public const string CountFunction = nameof(Count);

        private CounterState? _state;

        public override ValueTask ActivateAsync(KernelProcessStepState<CounterState> state)
        {
            this._state = state.State ?? new();
            Console.WriteLine($"Activating counter with value {this._state.Count}");
            return base.ActivateAsync(state);
        }

        [KernelFunction]
        public string Count()
        {
            this._state!.Count++;
            Console.WriteLine($"[COUNTER-{this.StepName}] {this._state.Count}");
            return this._state!.Count.ToString();
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
            /// Even number event name
            /// </summary>
            public const string EvenNumber = nameof(EvenNumber);
            /// <summary>
            /// Odd number event name
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
                Console.WriteLine($"[EVEN_NUMBER-{this.StepName}] {number}");
                await context.EmitEventAsync(OutputEvents.EvenNumber, numberString, KernelProcessEventVisibility.Public);
                return;
            }

            Console.WriteLine($"[ODD_NUMBER-{this.StepName}] {number}");
            await context.EmitEventAsync(OutputEvents.OddNumber, numberString, KernelProcessEventVisibility.Public);
        }
    }

    /// <summary>
    /// A step that echos its input.
    /// </summary>
    public sealed class EchoStep : KernelProcessStep
    {
        /// <summary>
        /// Output events emitted by <see cref="EchoStep"/>
        /// </summary>
        public static class OutputEvents
        {
            /// <summary>
            /// Echo message event name
            /// </summary>
            public const string EchoMessage = nameof(EchoMessage);
        }

        [KernelFunction]
        public async Task<string> EchoAsync(KernelProcessStepContext context, string message)
        {
            Console.WriteLine($"[ECHO-{this.StepName}] {message}");
            await context.EmitEventAsync(OutputEvents.EchoMessage, data: message, KernelProcessEventVisibility.Public);
            return message;
        }
    }

    /// <summary>
    /// A step that echos its input.
    /// </summary>
    public sealed class DualEchoStep : KernelProcessStep
    {
        /// <summary>
        /// Output events emitted by <see cref="EchoStep"/>
        /// </summary>
        public static class OutputEvents
        {
            /// <summary>
            /// Echo message event name
            /// </summary>
            public const string EchoMessage = nameof(EchoMessage);
        }

        [KernelFunction]
        public async Task<string> EchoAsync(KernelProcessStepContext context, string message1, string message2)
        {
            var message = $"{message1} {message2}";
            Console.WriteLine($"[DUAL-ECHO-{this.StepName}] {message}");
            await context.EmitEventAsync(OutputEvents.EchoMessage, data: message, KernelProcessEventVisibility.Public);
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
        public string MergeStrings(string str1, string str2, string str3)
        {
            Console.WriteLine($"[MERGE_STRINGS-{this.StepName}] {str1} {str2} {str3}");
            return string.Join(",", [str1, str2, str3]);
        }
    }
}
