// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel;

namespace ProductDocumentation.Steps;

public sealed class GenerateDocumentationStep : KernelProcessStep<GeneratedDocumentationState>
{
    private GeneratedDocumentationState _state = new();

    private string systemPrompt =
            """
            Your job is to write high quality and engaging customer facing documentation for a new product from Contoso. You will be provide with information
            about the product in the form of internal documentation, specs, and troubleshooting guides and you must use this information and
            nothing else to generate the documentation. If suggestions are provided on the documentation you create, take the suggestions into account and
            rewrite the documentation. Make sure the product sounds amazing.
            """;

    public override ValueTask ActivateAsync(KernelProcessStepState<GeneratedDocumentationState> state)
    {
        _state = state.State!;
        _state.ChatHistory ??= new ChatHistory(systemPrompt);

        return base.ActivateAsync(state);
    }

    [KernelFunction]
    public async Task<string?> GenerateDocumentation(Kernel kernel, KernelProcessStepContext context, string productInfo)
    {
        // Add the new product info to the chat history
        _state.ChatHistory!.AddUserMessage($"Product Info:\n\n{productInfo}");

        // Get a response from the LLM
        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var generatedDocumentationResponse = await chatCompletionService.GetChatMessageContentAsync(this._state.ChatHistory!);

        var documentationString = generatedDocumentationResponse.Content!.ToString();

        await context.EmitEventAsync("DocumentationGenerated", documentationString);

        return documentationString;
    }
}

public class GeneratedDocumentationState
{
    public ChatHistory? ChatHistory { get; set; }
}
