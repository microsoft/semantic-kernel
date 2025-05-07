// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;

namespace ProcessWithCloudEvents.Processes;

/// <summary>
/// Components related to the SK Process for generating documentation
/// </summary>
public static class TeacherStudentProcess
{
    /// <summary>
    /// The key that the process will be registered with in the SK process runtime.
    /// </summary>
    public static string Key => nameof(TeacherStudentProcess);

    /// <summary>
    /// SK Process events emitted by <see cref="DocumentGenerationProcess"/>
    /// </summary>
    public static class ProcessEvents
    {
        /// <summary>
        /// Event to start the document generation process
        /// </summary>
        public const string StartProcess = nameof(StartProcess);
        /// <summary>
        /// Event emitted when the user rejects the document
        /// </summary>
        public const string TeacherAskedQuestion = nameof(TeacherAskedQuestion);
    }

    /// <summary>
    /// SK Process topics emitted by <see cref="TeacherStudentProcess"/>
    /// Topics are used to emit events to external systems
    /// </summary>
    public static class InteractionTopics
    {
        /// <summary>
        /// Event emitted when the agent has a response
        /// </summary>
        public const string AgentResponseMessage = nameof(AgentResponseMessage);

        /// <summary>
        /// Event emitted when the agent has an error
        /// </summary>
        public const string AgentErrorMessage = nameof(AgentErrorMessage);
    }

    /// <summary>
    /// Creates a process builder for the Document Generation SK Process
    /// </summary>
    /// <param name="processName">name of the SK Process</param>
    /// <returns>instance of <see cref="ProcessBuilder"/></returns>
    public static ProcessBuilder CreateProcessBuilder(string processName = "TeacherStudentProcess")
    {
        // Create the process builder
        ProcessBuilder processBuilder = new(processName);

        // Add the steps
        var studentAgentStep = processBuilder.AddStepFromAgent(
            new()
            {
                Name = "Student",
                // On purpose not assigning AgentId, if not provided a new agent is created
                Description = "Solves problem given",
                Instructions = "Solve the problem given, if the question is repeated answer the question with a bit of humor emphasizing that the question was asked but still answering the question",
                Model = new()
                {
                    Id = "gpt-4o",
                },
                Type = OpenAIAssistantAgentFactory.OpenAIAssistantAgentType,
            });

        var proxyStep = processBuilder.AddProxyStep(id: "proxy", [InteractionTopics.AgentResponseMessage, InteractionTopics.AgentErrorMessage]);

        // Orchestrate the external input events
        processBuilder
            .OnInputEvent(ProcessEvents.StartProcess)
            //.SendEventTo(new(studentAgentStep, parameterName: "message"));
            .SentToAgentStep(studentAgentStep);

        processBuilder
            .OnInputEvent(ProcessEvents.TeacherAskedQuestion)
            //.SendEventTo(new(studentAgentStep, parameterName: "message"));
            .SentToAgentStep(studentAgentStep);

        studentAgentStep
            .OnFunctionResult()
            .EmitExternalEvent(proxyStep, InteractionTopics.AgentResponseMessage);

        studentAgentStep
            .OnFunctionError()
            .EmitExternalEvent(proxyStep, InteractionTopics.AgentErrorMessage)
            .StopProcess();

        return processBuilder;
    }
}
