# Simple Chat Summary Sample Learning App

> [!IMPORTANT]
> This sample will be removed in a future release. If you are looking for samples that demonstrate
> how to use Semantic Kernel, please refer to the sample folders in the root [python](../../../python/samples/)
> and [dotnet](../../../dotnet/samples/) folders.

Watch the [Chat Summary Quick Start Video](https://aka.ms/SK-Samples-SimChat-Video).

> **!IMPORTANT**
> This learning sample is for educational purposes only and should not be used in any
> production use case. It is intended to highlight concepts of Semantic Kernel and not
> any architectural / security design practices to be used.

## Running the sample

1. You will need an [OpenAI Key](https://openai.com/product/) or
   [Azure OpenAI Service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart)
   for this sample.
2. Ensure the KernelHttpServer sample is already running at `http://localhost:7071`. If not, follow the steps
   to start it [here](../../dotnet/KernelHttpServer/README.md).
3. Copy **[.env.example](.env.example)** into a new file with name "**.env**".
    > **Note**: Samples are configured to use chat completion AI models (e.g., gpt-3.5-turbo, gpt-4, etc.). See https://platform.openai.com/docs/models/model-endpoint-compatibility for chat completion model options.
4. You will also need to **Run** the following command `yarn install` (if you have never run the sample before)
   and/or `yarn start` from the command line.
5. A browser will automatically open, otherwise you can navigate to `http://localhost:3000` to use the sample.

> Working with Secrets: [KernelHttpServer's Readme](../../dotnet/KernelHttpServer/README.md#Working-with-Secrets) has a note on safely working with keys and other secrets.

## About the Simple Chat Summary Sample

The Simple Chat Summary sample allows you to see the power of semantic functions used in a chat.

The sample highlights the [SummarizeConversation](../../../dotnet/src/Plugins/Plugins.Core/SemanticFunctionConstants.cs#7), [GetConversationActionItems](../../../dotnet/src/Plugins/Plugins.Core/SemanticFunctionConstants.cs#20), and [GetConversationTopics](../../../dotnet/src/Plugins/Plugins.Core/SemanticFunctionConstants.cs#63)
native functions in the [Conversation Summary Skill](../../../dotnet/src/Plugins/Plugins.Core/ConversationSummaryPlugin.cs).
Each function calls Open AI to review the information in the chat window and produces insights.

The chat data can be loaded from this [data file](src/components/chat/ChatThread.ts) – which you
can edit or just add more to the chat while you are on the page.

> [!CAUTION]
> Each function will call Open AI which will use tokens that you will be billed for.

![chat-summary](https://user-images.githubusercontent.com/5111035/219096864-d5a42d13-7106-4d34-a084-f1db055f6686.gif)

## Next Steps: Try a more advanced sample app

[Book creator](../book-creator-webapp-react/README.md) – learn how Planner and chaining
of semantic functions can be used in your app.

## Deeper Learning Tips

-   Try modifying the array exported as ChatThread in
    [ChatThread.ts](src/components/chat/ChatThread.ts)
    to alter the conversation that is supplied by default.
-   View `loadSummarySkill`, `loadActionItemsSkill` and `loadTopicsSkill` in
    [ChatInteraction.tsx](src/components/chat/ChatInteraction.tsx)
    to see `fetch` requests that POST skills to the Semantic Kernel hosted by the
    [Azure Function](../../dotnet/KernelHttpServer/SemanticKernelEndpoint.cs)
-   Notice how [AISummary.tsx](src/components/AISummary.tsx) makes POST requests
    to the [Azure Function](../../dotnet/KernelHttpServer/SemanticKernelEndpoint.cs) to
    invoke skills that were previously added. Also take note of the Skill
    definition and configuration in Skills.ts - these skills were copied from the
    skills folder and added into the project to create a simple first run experience.
