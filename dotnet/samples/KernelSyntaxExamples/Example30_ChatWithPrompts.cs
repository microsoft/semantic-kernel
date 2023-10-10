// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.TemplateEngine.Basic;
using RepoUtils;
using Resources;

/**
 * Scenario:
 *  - the user is reading a wikipedia page, they select a piece of text and they ask AI to extract some information.
 *  - the app explicitly uses the Chat model to get a result.
 *
 * The following example shows how to:
 *
 * - Use the prompt template engine to render prompts, without executing them.
 *   This can be used to leverage the template engine (which executes functions internally)
 *   to generate prompts and use them programmatically, without executing them like semantic functions.
 *
 * - Use rendered prompts to create the context of System and User messages sent to Chat models
 *   like "gpt-3.5-turbo"
 *
 * Note: normally you would work with Semantic Functions to automatically send a prompt to a model
 *       and get a response. In this case we use the Chat model, sending a chat history object, which
 *       includes some instructions, some context (the text selected), and the user query.
 *
 *       We use the prompt template engine to craft the strings with all of this information.
 *
 *       Out of scope and not in the example: if needed, one could go further and use a semantic
 *       function (with extra cost) asking AI to generate the text to send to the Chat model.
 *
 * TLDR: how to render a prompt:
 *
 *      var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Logger).Build();
 *      ... import plugins and functions ...
 *      var context = kernel.CreateNewContext();
 *      ... set variables ...
 *
 *      var promptRenderer = new BasicPromptTemplateEngine();
 *      string renderedPrompt = await promptRenderer.RenderAsync("...prompt template...", context);
 */

// ReSharper disable CommentTypo
// ReSharper disable once InconsistentNaming
public static class Example30_ChatWithPrompts
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Chat with prompts ========");

        /* Load 3 files:
         * - 28-system-prompt.txt: the system prompt, used to initialize the chat session.
         * - 28-user-context.txt:  the user context, e.g. a piece of a document the user selected and is asking to process.
         * - 28-user-prompt.txt:   the user prompt, just for demo purpose showing that one can leverage the same approach also to augment user messages.
         */

        var systemPromptTemplate = EmbeddedResource.Read("30-system-prompt.txt");
        var selectedText = EmbeddedResource.Read("30-user-context.txt");
        var userPromptTemplate = EmbeddedResource.Read("30-user-prompt.txt");

        IKernel kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey, serviceId: "chat")
            .Build();

        // As an example, we import the time plugin, which is used in system prompt to read the current date.
        // We could also use a variable, this is just to show that the prompt can invoke functions.
        kernel.ImportFunctions(new TimePlugin(), "time");

        // We need a kernel context to store some information to pass to the prompts and the list
        // of available plugins needed to render prompt templates.
        var context = kernel.CreateNewContext();

        // Put the selected document into the variable used by the system prompt (see 28-system-prompt.txt).
        context.Variables["selectedText"] = selectedText;

        // Demo another variable, e.g. when the chat started, used by the system prompt (see 28-system-prompt.txt).
        context.Variables["startTime"] = DateTimeOffset.Now.ToString("hh:mm:ss tt zz", CultureInfo.CurrentCulture);

        // This is the user message, store it in the variable used by 28-user-prompt.txt
        context.Variables["userMessage"] = "extract locations as a bullet point list";

        // Instantiate the prompt renderer, which we will use to turn prompt templates
        // into strings, that we will store into a Chat history object, which is then sent
        // to the Chat Model.
        var promptRenderer = new BasicPromptTemplateEngine();

        // Render the system prompt. This string is used to configure the chat.
        // This contains the context, ie a piece of a wikipedia page selected by the user.
        string systemMessage = await promptRenderer.RenderAsync(systemPromptTemplate, context);
        Console.WriteLine($"------------------------------------\n{systemMessage}");

        // Render the user prompt. This string is the query sent by the user
        // This contains the user request, ie "extract locations as a bullet point list"
        string userMessage = await promptRenderer.RenderAsync(userPromptTemplate, context);
        Console.WriteLine($"------------------------------------\n{userMessage}");

        // Client used to request answers
        var chatGPT = kernel.GetService<IChatCompletion>();

        // The full chat history. Depending on your scenario, you can pass the full chat if useful,
        // or create a new one every time, assuming that the "system message" contains all the
        // information needed.
        var chatHistory = chatGPT.CreateNewChat(systemMessage);

        // Add the user query to the chat history
        chatHistory.AddUserMessage(userMessage);

        // Finally, get the response from AI
        string answer = await chatGPT.GenerateMessageAsync(chatHistory);
        Console.WriteLine($"------------------------------------\n{answer}");

        /*

        Output:

        ------------------------------------
        You are an AI assistant that helps people find information.
        The chat started at: 09:52:12 PM -07
        The current time is: Thursday, April 27, 2023 9:52 PM
        Text selected:
        The central Sahara is hyperarid, with sparse vegetation. The northern and southern reaches of the desert, along with the highlands, have areas of sparse grassland and desert shrub, with trees and taller shrubs in wadis, where moisture collects. In the central, hyperarid region, there are many subdivisions of the great desert: Tanezrouft, the Ténéré, the Libyan Desert, the Eastern Desert, the Nubian Desert and others. These extremely arid areas often receive no rain for years.
        ------------------------------------
        Thursday, April 27, 2023 2:34 PM: extract locations as a bullet point list
        ------------------------------------
        Sure, here are the locations mentioned in the text:

        - Tanezrouft
        - Ténéré
        - Libyan Desert
        - Eastern Desert
        - Nubian Desert

        */
    }
}
