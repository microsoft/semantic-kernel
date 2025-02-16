// Copyright (c) Microsoft. All rights reserved.

using OpenAI.Chat;

namespace ReasoningEffortModels;
// A smart blog post agent that asks for an analytical blog post about Semantic Kernel.
public class SmartBlogPostAgent : AgentBase
{
    public override string AgentName => "SmartBlogPostAgent";
    public override string AgentPrompt => "Write a smart, detailed blog post on Semantic Kernel that explains its architecture, benefits, and real-world applications.";
    public override string DefaultDeploymentName => "o3-mini";

    public SmartBlogPostAgent(ChatReasoningEffortLevel reasoningEffort)
        : base(reasoningEffort: reasoningEffort)
    {
    }
}

// A poem agent that asks for a creative poem about Semantic Kernel.
public class PoemAgent : AgentBase
{
    public override string AgentName => "PoemAgent";
    public override string AgentPrompt => "Compose a creative and whimsical poem about Semantic Kernel and its innovative approach to artificial intelligence.";
    public override string DefaultDeploymentName => "o3-mini";

    public PoemAgent(ChatReasoningEffortLevel reasoningEffort)
        : base(reasoningEffort: reasoningEffort)
    {
    }
}

// A code example agent that asks for sample code demonstrating the use of Semantic Kernel.
public class CodeExampleAgent : AgentBase
{
    public override string AgentName => "CodeExampleAgent";
    public override string AgentPrompt => "Provide a sample C# code snippet that demonstrates how to integrate Semantic Kernel into a creative project, including explanations for each step.";
    public override string DefaultDeploymentName => "o3-mini";

    public CodeExampleAgent(ChatReasoningEffortLevel reasoningEffort)
        : base(reasoningEffort: reasoningEffort)
    {
    }
}
