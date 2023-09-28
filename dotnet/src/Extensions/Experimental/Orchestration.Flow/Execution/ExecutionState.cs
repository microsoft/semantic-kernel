// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

/// <summary>
/// Execution state
/// </summary>
#pragma warning disable CA1724 // The type name conflicts
public sealed class ExecutionState
{
    /// <summary>
    /// Index of current step
    /// </summary>
    public int CurrentStepIndex { get; set; } = 0;

    /// <summary>
    /// Execution state described by variables.
    /// </summary>
    public Dictionary<string, string> Variables { get; set; } = new Dictionary<string, string>();

    /// <summary>
    /// Execution state of each step
    /// </summary>
    public Dictionary<string, StepExecutionState> StepStates { get; set; } = new Dictionary<string, StepExecutionState>();

    /// <summary>
    /// Step execution state
    /// </summary>
    public class StepExecutionState
    {
        /// <summary>
        /// The status of step execution
        /// </summary>
        public Status Status { get; set; } = Status.NotStarted;

        /// <summary>
        /// The execution count of step. The value could be larger than one if the step allows repeatable execution.
        /// </summary>
        public int ExecutionCount { get; set; }

        /// <summary>
        /// The output variables provided by the step
        /// </summary>
        public Dictionary<string, List<string>> Output { get; set; } = new Dictionary<string, List<string>>();

        /// <summary>
        /// Add or update variable for the step
        /// </summary>
        /// <param name="executionIndex">The execution index</param>
        /// <param name="key">The key of variable.</param>
        /// <param name="value">The value of variable.</param>
        public void AddOrUpdateVariable(int executionIndex, string key, string value)
        {
            var output = this.Output.GetOrAdd(key, new List<string>());
            if (output!.Count <= executionIndex)
            {
                output.Add(value);
            }
            else
            {
                output[executionIndex] = value;
            }
        }
    }

    /// <summary>
    /// The execution status enum
    /// </summary>
    public enum Status
    {
        /// <summary>
        /// Not started
        /// </summary>
        NotStarted,

        /// <summary>
        /// In progress
        /// </summary>
        InProgress,

        /// <summary>
        /// Completed
        /// </summary>
        Completed
    }
}
