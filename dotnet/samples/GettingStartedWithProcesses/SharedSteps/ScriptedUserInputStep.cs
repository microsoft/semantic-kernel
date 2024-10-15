// Copyright (c) Microsoft. All rights reserved.

using Events;
using Microsoft.SemanticKernel;

namespace SharedSteps;

/// <summary>
/// A step that elicits user input.
///
/// Step used in the Processes Samples:
/// - Step01_Processes.cs
/// - Step02_AccountOpening.cs
/// - Step04_AgentOrchestration
/// </summary>
public class ScriptedUserInputStep : KernelProcessStep<UserInputState>
{
    public static class Functions
    {
        public const string GetUserInput = nameof(GetUserInput);
    }

    protected bool SuppressOutput { get; init; }

    /// <summary>
    /// The state object for the user input step. This object holds the user inputs and the current input index.
    /// </summary>
    private readonly UserInputState _state = new();

    /// <summary>
    /// Method to be overridden by the user to populate with custom user messages
    /// </summary>
    /// <param name="state">The initialized state object for the step.</param>
    public virtual void PopulateUserInputs(UserInputState state)
    {
        return;
    }

    /// <summary>
    /// Activates the user input step by initializing the state object. This method is called when the process is started
    /// and before any of the KernelFunctions are invoked.
    /// </summary>
    /// <param name="state">The state object for the step.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    public override ValueTask ActivateAsync(KernelProcessStepState<UserInputState> state)
    {
        state.State ??= _state;

        PopulateUserInputs(_state);

        return ValueTask.CompletedTask;
    }

    /// <summary>
    /// Gets the user input.
    /// </summary>
    /// <param name="context">An instance of <see cref="KernelProcessStepContext"/> which can be
    /// used to emit events from within a KernelFunction.</param>
    /// <returns>A <see cref="ValueTask"/></returns>
    [KernelFunction(Functions.GetUserInput)]
    public async ValueTask GetUserInputAsync(KernelProcessStepContext context)
    {
        if (_state.CurrentInputIndex >= _state.UserInputs.Count)
        {
            // Emit the completion event
            await context.EmitEventAsync(new() { Id = CommonEvents.UserInputComplete });
            return;
        }

        string userMessage = _state.UserInputs[_state.CurrentInputIndex];
        _state.CurrentInputIndex++;

        if (!this.SuppressOutput)
        {
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine($"USER: {userMessage}");
            Console.ResetColor();
        }

        // Emit the user input
        await context.EmitEventAsync(new() { Id = CommonEvents.UserInputReceived, Data = userMessage });
    }
}

/// <summary>
/// The state object for the <see cref="ScriptedUserInputStep"/>
/// </summary>
public record UserInputState
{
    public List<string> UserInputs { get; init; } = [];

    public int CurrentInputIndex { get; set; } = 0;
}
