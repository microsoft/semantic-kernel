// Copyright (c) Microsoft. All rights reserved.

using SharedSteps;

namespace Step02.Steps;

/// <summary>
/// <see cref="ScriptedUserInputStep"/> Step with interactions that makes the Process pass all steps and successfully open a new account
/// </summary>
public sealed class UserInputSuccessfulInteractionStep : ScriptedUserInputStep
{
    public override void PopulateUserInputs(UserInputState state)
    {
        state.UserInputs.Add("I would like to open an account");
        state.UserInputs.Add("My name is John Contoso, dob 02/03/1990");
        state.UserInputs.Add("I live in Washington and my phone number es 222-222-1234");
        state.UserInputs.Add("My userId is 987-654-3210");
        state.UserInputs.Add("My email is john.contoso@contoso.com, what else do you need?");
    }
}
