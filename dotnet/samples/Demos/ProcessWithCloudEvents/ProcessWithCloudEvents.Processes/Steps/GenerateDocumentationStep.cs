// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
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

    internal GenerateDocumentationState? _state = new();

    /// <inheritdoc/>
    public override ValueTask ActivateAsync(KernelProcessStepState<GenerateDocumentationState> state)
    {
        this._state = state.State;
        return base.ActivateAsync(state);
    }

    [KernelFunction(Functions.GenerateDocs)]
    public async Task OnGenerateDocumentationAsync(KernelProcessStepContext context, ProductInfo content)
    {
        DocumentInfo generatedContent = new()
        {
            Id = Guid.NewGuid().ToString(),
            Title = $"Generated document - {content.Title}",
            Content = $"Generated {content.Content}",
        };

        this._state!.LastGeneratedDocument = generatedContent;

        await context.EmitEventAsync(OutputEvents.DocumentationGenerated, generatedContent);
    }

    [KernelFunction(Functions.ApplySuggestions)]
    public async Task ApplySuggestionsAsync(KernelProcessStepContext context, string suggestions)
    {
        DocumentInfo updatedContent = new()
        {
            Id = Guid.NewGuid().ToString(),
            Title = $"Revised - {this._state?.LastGeneratedDocument.Title}",
            Content = $"{suggestions} + {this._state?.LastGeneratedDocument.Content}",
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
}
