// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.TemplateEngine;
using Planning.IterativePlanner;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

public class IterativePlannerChat : IterativePlannerText
{
    private readonly string _systemPromptTemplate;
    private readonly string _userPromptTemplate;

    public IterativePlannerChat(IKernel kernel,
        int maxIterations = 5,
        string? systemPrompt = null,
        string systemResource = "iterative-planer-chat-system.txt",
        string? userPrompt = null,
        string userResource = "iterative-planer-chat-user.txt"
    )
        : base(kernel, maxIterations, null, null)
    {
        if (!string.IsNullOrEmpty(systemResource))
        {
            this._systemPromptTemplate = EmbeddedResource.Read(systemResource);
        }

        if (!string.IsNullOrEmpty(userResource))
        {
            this._userPromptTemplate = EmbeddedResource.Read(userResource);
        }

        if (!string.IsNullOrEmpty(systemPrompt))
        {
            this._systemPromptTemplate = systemPrompt;
        }

        if (!string.IsNullOrEmpty(userPrompt))
        {
            this._userPromptTemplate = userPrompt;
        }
    }

    public override async Task<string> ExecutePlanAsync(string goal)
    {
        IChatCompletion chat = this.Kernel.GetService<IChatCompletion>();

        var promptRenderer = new PromptTemplateEngine();
        var context = this.Kernel.CreateNewContext();

        (string toolNames, string toolDescriptions) = this.GetToolNamesAndDescriptions();

        context.Variables.Set("toolNames", toolNames);
        context.Variables.Set("toolDescriptions", toolDescriptions);
        context.Variables.Set("question", goal);

        var chatRequestSettings = new ChatRequestSettings
        {
            MaxTokens = this.MaxTokens,
            StopSequences = new List<string>() { "Observation:" },
            Temperature = 0
        };

        var systemPrompt = await promptRenderer.RenderAsync(this._systemPromptTemplate, context).ConfigureAwait(false);

        for (int i = 0; i < this.MaxIterations; i++)
        {
            var chatHistory = (OpenAIChatHistory)chat.CreateNewChat(systemPrompt);
            var scratchPad = this.CreateScratchPad(goal);
            context.Variables.Set("agentScratchPad", scratchPad);
            var userMessage = await promptRenderer.RenderAsync(this._userPromptTemplate, context).ConfigureAwait(false);
            PrintColored(scratchPad);

            chatHistory.AddUserMessage(userMessage);

            string reply = await chat.GenerateMessageAsync(chatHistory, chatRequestSettings).ConfigureAwait(false);
        
            var nextStep = this.ParseResult(reply);
            this.Steps.Add(nextStep);

            if (!String.IsNullOrEmpty(nextStep.FinalAnswer))
            {
                return nextStep.FinalAnswer;
            }

            nextStep.Observation = await this.InvokeActionAsync(nextStep.Action, nextStep.ActionInput).ConfigureAwait(false);
        }

        return "zebra";

        //return base.ExecutePlanAsync(goal);
    }
}
