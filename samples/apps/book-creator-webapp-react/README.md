# Book Creator Sample Learning App

> [!IMPORTANT]
> This sample will be removed in a future release. If you are looking for samples that demonstrate
> how to use Semantic Kernel, please refer to the sample folders in the root [python](../../../python/samples/)
> and [dotnet](../../../dotnet/samples/) folders.

> **!IMPORTANT**
> This learning sample is for educational purposes only and should not be used in any
> production use case. It is intended to highlight concepts of Semantic Kernel and not
> any architectural / security design practices to be used.

### Watch the Book Creator Sample Quick Start [Video](https://aka.ms/SK-Book-Creator).

## Running the sample

1. You will need an [Open AI Key](https://openai.com/api/) or
   [Azure Open AI Service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart)
   for this sample.
2. Ensure the KernelHttpServer sample is already running at `http://localhost:7071`. If not, follow the steps
   to start it [here](../../dotnet/KernelHttpServer/README.md).
3. Copy **[.env.example](.env.example)** into a new file with name "**.env**".
    > **Note**: Samples are configured to use chat completion AI models (e.g., gpt-3.5-turbo, gpt-4, etc.). See https://platform.openai.com/docs/models/model-endpoint-compatibility for chat completion model options.
4. You will also need to **Run** the following command `yarn install` (if you have never run the sample before)
   and/or `yarn start` from the command line.
5. A browser will automatically open, otherwise you can navigate to `http://localhost:3000` to use the sample.

> Working with Secrets: [KernelHttpServer's Readme](../../dotnet/KernelHttpServer/README.md#Working-with-Secrets) has a note on safely working with keys and other secrets.

## About the Book Creator Sample

The Book creator sample allows you to enter in a topic then the
[Planner](https://aka.ms/sk/concepts/planner)
creates a plan for the functions to run based on the ask. You can see the plan along with the results.

> [!CAUTION]
> Each function will call Open AI which will use tokens that you will be billed for.

![book-sample-app](https://user-images.githubusercontent.com/5111035/219122383-6ee0e015-1251-4951-8a00-2c319ab034ca.gif)

## Next Steps: Try the sample showing off how authentication and API calls work

[Authentication and APIs](../auth-api-webapp-react/README.md) – learn how to connect
to external API's with authentication while using Semantic Kernel.

## Deeper Learning Tips

-   Try modifying the language that the book is translated to via editing
    the `translateToLanguage` constant in [CreateBook.tsx](src/components/CreateBook.tsx)
-   View `fetchTopics` in [TopicSelection.tsx](src/components/TopicSelection.tsx) to see
    how input variables are being fed to the ask. Try changing the number.

Next we will have a version of the sample that incorporates the planner functionality.
