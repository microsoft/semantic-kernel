// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using ProcessWithCloudEvents.Processes.Models;

namespace ProcessWithCloudEvents.Processes.Steps;

/// <summary>
/// Step that generates document content
/// </summary>
public class GenerateDocumentationStep : KernelProcessStep<GenerateDocumentationState>
{
    /// <summary>
    /// Function names of the steps, to be refereced when hooking up the step in a SK process
    /// </summary>
    public static class Functions
    {
        /// <summary>
        /// Genereta Doc function name
        /// </summary>
        public const string GenerateDocs = nameof(GenerateDocs);
        /// <summary>
        /// Apply Suggestions function name
        /// </summary>
        public const string ApplySuggestions = nameof(ApplySuggestions);
    }

    /// <summary>
    /// Output events of the step, using this since 2 steps emit the same output event
    /// </summary>
    public static class OutputEvents
    {
        /// <summary>
        /// Document Generated output event
        /// </summary>
        public const string DocumentationGenerated = nameof(DocumentationGenerated);
    }

    internal GenerateDocumentationState _state = new();

    private readonly string _systemPrompt =
        """
        Your job is to write high quality and engaging customer facing documentation for a new product from Contoso. You will be provide with information
        about the product in the form of internal documentation, specs, and troubleshooting guides and you must use this information and
        nothing else to generate the documentation. If suggestions are provided on the documentation you create, take the suggestions into account and
        rewrite the documentation. Make sure the product sounds amazing.
        """;

    /// <inheritdoc/>
    public override ValueTask ActivateAsync(KernelProcessStepState<GenerateDocumentationState> state)
    {
        this._state = state.State!;
        this._state.ChatHistory ??= new ChatHistory(this._systemPrompt);

        return base.ActivateAsync(state);
    }

    /// <summary>
    /// Function that generates documentation from the <see cref="ProductInfo"/> provided
    /// </summary>
    /// <param name="kernel">instance of <see cref="Kernel"/></param>
    /// <param name="context">instance of <see cref="KernelProcessStepContext"/></param>
    /// <param name="productInfo">content to be used for document generation</param>
    /// <returns></returns>
    [KernelFunction(Functions.GenerateDocs)]
    public async Task GenerateDocumentationAsync(Kernel kernel, KernelProcessStepContext context, ProductInfo productInfo)
    {
        Console.WriteLine($"[{nameof(GenerateDocumentationStep)}]:\tGenerating documentation for provided productInfo...");

        // Add the new product info to the chat history
        this._state.ChatHistory!.AddUserMessage($"Product Info:\n{productInfo.Title} - {productInfo.Content}");

        // Get a response from the LLM
        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var generatedDocumentationResponse = await chatCompletionService.GetChatMessageContentAsync(this._state.ChatHistory!);

        DocumentInfo generatedContent = new()
        {
            Id = Guid.NewGuid().ToString(),
            Title = $"Generated document - {productInfo.Title}",
            Content = generatedDocumentationResponse.Content!,
        };

        this._state!.LastGeneratedDocument = generatedContent;

        await context.EmitEventAsync(OutputEvents.DocumentationGenerated, generatedContent);
    }

    /// <summary>
    /// Function that integrates suggestion into document content
    /// </summary>
    /// <param name="kernel">instance of <see cref="Kernel"/></param>
    /// <param name="context">instance of <see cref="KernelProcessStepContext"/></param>
    /// <param name="suggestions">suggestions to be integrated into the document content</param>
    /// <returns></returns>
    [KernelFunction(Functions.ApplySuggestions)]
    public async Task ApplySuggestionsAsync(Kernel kernel, KernelProcessStepContext context, string suggestions)
    {
        Console.WriteLine($"[{nameof(GenerateDocumentationStep)}]:\tRewriting documentation with provided suggestions...");

        // Add the new product info to the chat history
        this._state.ChatHistory!.AddUserMessage($"Rewrite the documentation with the following suggestions:\n\n{suggestions}");

        // Get a response from the LLM
        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var generatedDocumentationResponse = await chatCompletionService.GetChatMessageContentAsync(this._state.ChatHistory!);

        DocumentInfo updatedContent = new()
        {
            Id = Guid.NewGuid().ToString(),
            Title = $"Revised - {this._state?.LastGeneratedDocument.Title}",
            Content = generatedDocumentationResponse.Content!,
        };

        this._state!.LastGeneratedDocument = updatedContent;

        await context.EmitEventAsync(OutputEvents.DocumentationGenerated, updatedContent);
    }
}

/// <summary>
/// State of <see cref="GenerateDocumentationStep"/>
/// State must be saved since data is shared across functions
/// </summary>
public sealed class GenerateDocumentationState
{
    /// <summary>
    /// Last Document generated data
    /// </summary>
    public DocumentInfo LastGeneratedDocument { get; set; } = new();

    /// <summary>
    /// Chat history
    /// </summary>
    public ChatHistory? ChatHistory { get; set; }
}
