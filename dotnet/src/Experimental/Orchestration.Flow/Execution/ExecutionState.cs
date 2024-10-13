// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

/// <summary>
/// Execution state
/// </summary>
public sealed class ExecutionState
{
    /// <summary>
    /// Index of current step
    /// </summary>
    public int CurrentStepIndex { get; set; } = 0;

    /// <summary>
    /// Execution state described by variables.
    /// </summary>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public Dictionary<string, string> Variables { get; set; } = [];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    public Dictionary<string, string> Variables { get; set; } = [];
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
    public Dictionary<string, string> Variables { get; set; } = [];
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
    public Dictionary<string, string> Variables { get; set; } = [];
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    public Dictionary<string, string> Variables { get; set; } = [];
=======
    public Dictionary<string, string> Variables { get; set; } = new Dictionary<string, string>();
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

    /// <summary>
    /// Execution state of each step
    /// </summary>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public Dictionary<string, StepExecutionState> StepStates { get; set; } = [];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    public Dictionary<string, StepExecutionState> StepStates { get; set; } = [];
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
    public Dictionary<string, StepExecutionState> StepStates { get; set; } = [];
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
    public Dictionary<string, StepExecutionState> StepStates { get; set; } = [];
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    public Dictionary<string, StepExecutionState> StepStates { get; set; } = [];
=======
    public Dictionary<string, StepExecutionState> StepStates { get; set; } = new Dictionary<string, StepExecutionState>();
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

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
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        public Dictionary<string, List<string>> Output { get; set; } = [];
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        public Dictionary<string, List<string>> Output { get; set; } = [];
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        public Dictionary<string, List<string>> Output { get; set; } = [];
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        public Dictionary<string, List<string>> Output { get; set; } = [];
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        public Dictionary<string, List<string>> Output { get; set; } = [];
=======
        public Dictionary<string, List<string>> Output { get; set; } = new Dictionary<string, List<string>>();
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        /// <summary>
        /// Add or update variable for the step
        /// </summary>
        /// <param name="executionIndex">The execution index</param>
        /// <param name="key">The key of variable.</param>
        /// <param name="value">The value of variable.</param>
        public void AddOrUpdateVariable(int executionIndex, string key, string value)
        {
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> head
            if (!this.Output.TryGetValue(key, out List<string>? output))
            {
                this.Output[key] = output = [];
            }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
            var output = this.Output.GetOrAdd(key, new List<string>());
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> Stashed changes
=======
=======
            var output = this.Output.GetOrAdd(key, new List<string>());
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> Stashed changes
=======
=======
            var output = this.Output.GetOrAdd(key, new List<string>());
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> Stashed changes
=======
=======
            var output = this.Output.GetOrAdd(key, new List<string>());
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> Stashed changes
=======
=======
            var output = this.Output.GetOrAdd(key, new List<string>());
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> Stashed changes
=======
=======
            var output = this.Output.GetOrAdd(key, new List<string>());
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> Stashed changes
=======
=======
            var output = this.Output.GetOrAdd(key, new List<string>());
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
            var output = this.Output.GetOrAdd(key, new List<string>());
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> Stashed changes
=======
=======
            var output = this.Output.GetOrAdd(key, new List<string>());
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> Stashed changes
>>>>>>> head
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
