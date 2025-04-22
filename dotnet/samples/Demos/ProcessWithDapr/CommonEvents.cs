// Copyright (c) Microsoft. All rights reserved.

namespace ProcessWithDapr;

internal static class CommonEvents
{
    public const string UserInputReceived = nameof(UserInputReceived);
    public const string CompletionResponseGenerated = nameof(CompletionResponseGenerated);
    public const string WelcomeDone = nameof(WelcomeDone);
    public const string AStepDone = nameof(AStepDone);
    public const string BStepDone = nameof(BStepDone);
    public const string CStepDone = nameof(CStepDone);
    public const string StartARequested = nameof(StartARequested);
    public const string StartBRequested = nameof(StartBRequested);
    public const string ExitRequested = nameof(ExitRequested);
    public const string StartProcess = nameof(StartProcess);
}
