// Copyright (c) Microsoft. All rights reserved.
namespace Events;

/// <summary>
/// Processes Events emitted by shared steps.<br/>
/// </summary>
public static class CommonEvents
{
    public static readonly string UserInputReceived = nameof(UserInputReceived);
    public static readonly string UserInputComplete = nameof(UserInputComplete);
    public static readonly string AssistantResponseGenerated = nameof(AssistantResponseGenerated);
    public static readonly string Exit = nameof(Exit);
}
