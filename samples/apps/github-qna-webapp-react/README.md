# GitHub Repo Q&A Bot Sample

> **!IMPORTANT**
> This learning sample is for educational purposes only and should not be used in any
> production use case. It is intended to highlight concepts of Semantic Kernel and not
> any architectural / security design practices to be used.

## Running the sample

1. You will need an [Open AI Key](https://openai.com/api/) or
   [Azure Open AI Service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart)
   for this sample.
2. Ensure the service API is already running `http://localhost:7071`. If not, learn
   how to start it [here](../../dotnet/KernelHttpServer/README.md).
3. You will also need to Copy **[.env.example](.env.example)** into a new file with name "**.env**".
   > **Note**: Samples are configured to use chat completion AI models (e.g., gpt-3.5-turbo, gpt-4, etc.). See https://platform.openai.com/docs/models/model-endpoint-compatibility for chat completion model options.
4. **Run** the following command `yarn install` (if you have never run the sample before)
   and/or `yarn start` from the command line.
5. A browser will open or you can navigate to `http://localhost:3000` to use the sample.

> Working with Secrets: [KernelHttpServer's Readme](../../dotnet/KernelHttpServer/README.md#Working-with-Secrets) has a note on safely working with keys and other secrets.

## About the GitHub Repo Q&A Bot Sample

The GitHub Repo Q&A Bot sample allows you to pull in data from a public GitHub
repo into a local memory store in order to ask questions about the project and
to get answers about it. The sample highlights how [memory](https://aka.ms/sk/memories)
and [embeddings](https://aka.ms/sk/embeddings) work along with the
[TextChunker](../../../dotnet/src/SemanticKernel/Text/TextChunker.cs)
when the size of the data is larger than the allowed token limited.
Each SK function will call Open AI to perform the tasks you ask about.

In order to reduce costs and improve overall performance, this sample app indexes
only content extracted from markdown files.

> [!CAUTION]
> Each function will call Open AI which will use tokens that you will be billed for.

## Working with private repositories
The GitHub Repo Q&A Bot sample allows you to pull in data from private a GitHub repo. To do so, you must create a [fine-grained personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token) if you have not already. The token must have access to the repository you are trying to pull data from and Contents read access to the repository:
![Alt text](image-1.png)


## Next Steps

Create Skills and SK functions: Check out the [documentation](https://aka.ms/sk/learn)
for how to create Skills.

Join the community: Join our [Discord community](https://aka.ms/SKDiscord) to
share ideas and get help​.

Contribute: We need your help to make this the best it can be. Learn how you
can [contribute](https://github.com/microsoft/semantic-kernel/blob/main/CONTRIBUTING.md)
to this project.​
