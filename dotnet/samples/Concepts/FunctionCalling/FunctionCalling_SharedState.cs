// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Resources;

namespace FunctionCalling;

/// <summary>
/// This sample demonstrates the way SK plugins can share local state to save and retrieve data.
/// </summary>
public class FunctionCalling_SharedState(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This sample demonstrates a scenario where a text is summarized, translated, and printed to the console.
    /// The process is orchestrated by an AI model that calls plugins to execute each step.
    /// When the first plugin is called, it summarizes the provided text and stores it in the local state, returning a state ID to the AI model.
    /// The next plugin is called to translate the text stored in the local state using the state ID returned by the first plugin.
    /// The plugin translates the text and stores the translation in the local state as well, returning a new state ID to the AI model.
    /// The last plugin is called by the AI model to print the translated text to the console using the state ID returned by the second plugin.
    /// </summary>
    [Fact]
    public async Task SaveSharedStateInLocalStoreAsync()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);

        // Register the output helper used by the ConsolePlugin
        builder.Services.AddSingleton(this.Output);

        // Register the state service
        builder.Services.AddSingleton<LocalStateService>();

        // Register the plugins
        builder.Plugins.AddFromType<SummarizationPlugin>();
        builder.Plugins.AddFromType<TranslationPlugin>();
        builder.Plugins.AddFromType<ConsolePlugin>();

        Kernel kernel = builder.Build();

        // Enable function calling
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Call the AI model to summarize, translate, and print the translation
        string textToSummarizeAndTranslate = EmbeddedResource.Read("travel-destination-overview.txt");

        FunctionResult result = await kernel.InvokePromptAsync($"Summarize the text, translate to English and display the result: {textToSummarizeAndTranslate}", new(settings));

        Console.WriteLine(result);

        // Expected output: Ireland is an attractive travel destination with impressive landscapes, rich culture, and famous attractions such as Dublin, Trinity College, the Book of Kells, and the Guinness Storehouse.
        // In addition to urban experiences, it offers nature enthusiasts numerous outdoor activities, such as exploring the Ring of Kerry, the Cliffs of Moher, and numerous national parks and hiking trails.
    }

    private sealed class SummarizationPlugin(LocalStateService stateService)
    {
        [KernelFunction, Description("Summarize the text and store the summary in state. Returns the state ID.")]
        public async Task<string> Summarize(Kernel kernel, string text)
        {
            // Use AI model to summarize the text
            FunctionResult result = await kernel.InvokePromptAsync($"Summarize the key points of the text in two sentences: {text}");

            // Store the summary in state
            string stateId = Guid.NewGuid().ToString();

            stateService.SetState(stateId, result.ToString());

            return stateId;
        }
    }

    private sealed class TranslationPlugin(LocalStateService stateService)
    {
        [KernelFunction, Description("Translate the text from state identified by stateId to the specified language and store the translation in state. Returns the state ID.")]
        public async Task<string> Translate(Kernel kernel, string stateId, string language)
        {
            // Retrieve the text for translation from state
            string textToTranslate = stateService.GetState(stateId);

            // Use AI model to translate the text. Alternatively, a translation service could be used.
            FunctionResult result = await kernel.InvokePromptAsync($"Translate the text: {textToTranslate} to {language}");

            // Store the translation in state
            string targetStateId = Guid.NewGuid().ToString();

            stateService.SetState(targetStateId, result.ToString());

            return targetStateId;
        }
    }

    private sealed class ConsolePlugin(LocalStateService stateService, ITestOutputHelper outputHelper)
    {
        [KernelFunction, Description("Print the text from state identified by stateId to the console.")]
        public void Print(string stateId)
        {
            // Retrieve the text from state
            string text = stateService.GetState(stateId);

            outputHelper.WriteLine(text);
        }
    }

    private sealed class LocalStateService
    {
        private readonly Dictionary<string, string> _state = [];

        public string GetState(string id)
        {
            if (this._state.TryGetValue(id, out string? value))
            {
                return value;
            }
            throw new KeyNotFoundException($"State with ID {id} not found.");
        }

        public void SetState(string id, string value)
        {
            this._state[id] = value;
        }
    }
}
