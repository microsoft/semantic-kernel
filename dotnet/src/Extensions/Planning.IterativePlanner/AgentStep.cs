// Copyright (c) Microsoft. All rights reserved.

namespace Planning.IterativePlanner;

public class AgentStep   
{
    public string? Thought { get; set; }
    public string? Action { get; set; }
    public string? ActionInput { get; set; }
    public string? Observation { get; set; }
    public string? FinalAnswer { get; set; }
    public string? OriginalResponse { get; set; }
}
