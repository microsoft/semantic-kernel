// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ProcessWithCloudEvents.Processes.Steps;

public class GenerateDocumentationStep : KernelProcessStep<GenerateDocumentationState>
{
    /// <summary>
    /// Function names of the steps, to be refereced when hooking up the step in a SK process
    /// </summary>
    public static class Functions
    {
        public const string GenerateDocs = nameof(GenerateDocs);
        public const string ApplySuggestions = nameof(ApplySuggestions);
    }

    /// <summary>
    /// Output events of the step, using this since 2 steps emit the same output event
    /// </summary>
    public static class OutputEvents
    {
        public const string DocumentationGenerated = nameof(DocumentationGenerated);
    }

    internal GenerateDocumentationState? _state = new();

    public override ValueTask ActivateAsync(KernelProcessStepState<GenerateDocumentationState> state)
    {
        this._state = state.State;
        return base.ActivateAsync(state);
    }

    [KernelFunction(Functions.GenerateDocs)]
    public async Task OnGenerateDocumentationAsync(KernelProcessStepContext context, string content)
    {
        var generatedContent = $"Generated {content}";
        this._state!.LastGeneratedDocument = generatedContent;

        await context.EmitEventAsync(OutputEvents.DocumentationGenerated, generatedContent);
    }

    [KernelFunction(Functions.ApplySuggestions)]
    public async Task ApplySuggestionsAsync(KernelProcessStepContext context, string suggestions)
    {
        var updatedContent = $"{suggestions} + {this._state?.LastGeneratedDocument}";
        this._state!.LastGeneratedDocument = updatedContent;

        await context.EmitEventAsync(OutputEvents.DocumentationGenerated, updatedContent);
    }
}

public sealed class GenerateDocumentationState
{
    public string LastGeneratedDocument = string.Empty;
}
