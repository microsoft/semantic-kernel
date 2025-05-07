// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Processes.Steps;

/// <summary>
/// Step that determines generated document readiness
/// </summary>
public class ProofReadDocumentationStep : KernelProcessStep
{
    /// <summary>
    /// SK Process Events emitted by <see cref="ProofReadDocumentationStep"/>
    /// </summary>
    public static class OutputEvents
    {
        /// <summary>
        /// Document has errors and needs to be revised event
        /// </summary>
        public const string DocumentationRejected = nameof(DocumentationRejected);
        /// <summary>
        /// Document looks ok and can be processed by the next step
        /// </summary>
        public const string DocumentationApproved = nameof(DocumentationApproved);
    }

    private readonly string _systemPrompt = """"
        Your job is to proofread customer facing documentation for a new product from Contoso. You will be provide with proposed documentation
        for a product and you must do the following things:

        1. Determine if the documentation is passes the following criteria:
            1. Documentation must use a professional tone.
            1. Documentation should be free of spelling or grammar mistakes.
            1. Documentation should be free of any offensive or inappropriate language.
            1. Documentation should be technically accurate.
        2. If the documentation does not pass 1, you must write detailed feedback of the changes that are needed to improve the documentation. 
        """";

    /// <summary>
    /// Determines whether the document is needs a revision or is ready to be processed by the next step
    /// </summary>
    /// <param name="kernel">instance of <see cref="Kernel"/></param>
    /// <param name="context">instance of <see cref="KernelProcessStepContext"/></param>
    /// <param name="document">document content that is verified</param>
    /// <returns></returns>
    [KernelFunction]
    public async Task ProofreadDocumentationAsync(Kernel kernel, KernelProcessStepContext context, DocumentInfo document)
    {
        var chatHistory = new ChatHistory(this._systemPrompt);
        chatHistory.AddUserMessage(document.Content);

        // Use structured output to ensure the response format is easily parsable
        var settings = new OpenAIPromptExecutionSettings()
        {
            ResponseFormat = typeof(ProofreadingResponse)
        };

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var proofreadResponse = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings: settings);
        var formattedResponse = JsonSerializer.Deserialize<ProofreadingResponse>(proofreadResponse.Content!);

        Console.WriteLine($"[{nameof(ProofReadDocumentationStep)}]:\n\tGrade = {(formattedResponse!.MeetsExpectations ? "Pass" : "Fail")}\n\tExplanation = {formattedResponse.Explanation}\n\tSuggestions = {string.Join("\n\t\t", formattedResponse.Suggestions)}");

        if (formattedResponse.MeetsExpectations)
        {
            // Events that are getting piped to steps that will be resumed, like PublishDocumentationStep.OnPublishDocumentation
            // require events to be marked as public so they are persisted and restored correctly
            await context.EmitEventAsync(OutputEvents.DocumentationApproved, data: document, visibility: KernelProcessEventVisibility.Public);
        }
        else
        {
            await context.EmitEventAsync(new()
            {
                Id = OutputEvents.DocumentationRejected,
                // This event is getting piped to the GenerateDocumentationStep.ApplySuggestionsAsync step which expects a string with suggestions for the document
                Data = $"Explanation = {formattedResponse.Explanation}, Suggestions = {string.Join(",", formattedResponse.Suggestions)} ",
            });
        }
    }

    private sealed class ProofreadingResponse
    {
        [Description("Specifies if the proposed documentation meets the expected standards for publishing.")]
        public bool MeetsExpectations { get; set; }

        [Description("An explanation of why the documentation does or does not meet expectations.")]
        public string Explanation { get; set; } = "";

        [Description("A lis of suggestions, may be empty if there no suggestions for improvement.")]
        public List<string> Suggestions { get; set; } = [];
    }
}
