// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

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

        /// English translation of the text below:
        /// Ireland is a popular travel destination for tourists from all over the world, known for its breathtaking landscapes, rich culture, and warm hospitality. The green island offers a variety of attractions,
        /// including historic castles, picturesque coastlines, and vibrant cities. Dublin, the capital, is a bustling center with a mix of history and modern life. Tourists can visit the famous Trinity College,
        /// admire the Book of Kells, or explore the Guinness Storehouse, where they can learn more about the world-famous Irish beer.
        ///
        ///In addition to urban attractions, Ireland also offers numerous opportunities for nature and outdoor enthusiasts.The Ring of Kerry is one of the country's most well-known scenic routes, leading through
        ///stunning landscapes, past charming villages, and historic sites. The Cliffs of Moher, rising majestically over the Atlantic Ocean, are another highlight that shouldn't be missed.Hikers and cyclists will
        ///find ideal conditions to experience Ireland's natural beauty in the many national parks and on the hiking trails, such as the Wicklow Way.
        string textToSummarizeAndTranslate =
            "Irland ist ein beliebtes Reiseziel für Touristen aus aller Welt, bekannt für seine atemberaubende Landschaft, reiche Kultur und herzliche Gastfreundschaft. Die grüne Insel bietet eine Vielzahl von" +
            " Sehenswürdigkeiten, darunter historische Schlösser, malerische Küstenlinien und lebendige Städte. Dublin, die Hauptstadt, ist ein pulsierendes Zentrum mit einer Mischung aus Geschichte und modernem Leben. " +
            "Touristen können das berühmte Trinity College besuchen, das Book of Kells bewundern oder das Guinness Storehouse erkunden, wo sie mehr über das weltberühmte irische Bier erfahren können." +
            "\n\n" +
            "Neben den städtischen Attraktionen bietet Irland auch zahlreiche Möglichkeiten für Natur- und Outdoor-Enthusiasten. Der Ring of Kerry ist eine der bekanntesten Panoramarouten des Landes und führt durch " +
            "atemberaubende Landschaften, vorbei an malerischen Dörfern und historischen Stätten. Die Cliffs of Moher, die sich majestätisch über den Atlantischen Ozean erheben, sind ein weiteres Highlight, das man " +
            "nicht verpassen sollte. Wanderer und Radfahrer finden in den vielen Nationalparks und auf den Wanderwegen, wie dem Wicklow Way, ideale Bedingungen, um die natürliche Schönheit Irlands zu erleben.";

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
