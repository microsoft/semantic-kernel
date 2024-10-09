// Copyright (c) Microsoft. All rights reserved.
namespace Step04.Models;

/// <summary>
/// Processes Events related to Account Opening scenarios.<br/>
/// Class used in <see cref="Step04_AgentOrchestration"/> samples
/// </summary>
public static class AgentOrchestrationEvents
{
    public static readonly string StartProcess = nameof(StartProcess);

    public static readonly string UserInput = nameof(UserInput);
    public static readonly string UserConfirmation = nameof(UserConfirmation);
    public static readonly string UserDone = nameof(UserDone);
    public static readonly string ManagerAgentResponded = nameof(ManagerAgentResponded);
    public static readonly string ManagerAgentWorking = nameof(ManagerAgentWorking);
    public static readonly string WorkerAgentResponded = nameof(WorkerAgentResponded);
}
