# GitHub Repo Q&A Bot Sample

> **!IMPORTANT**
> This learning sample is for educational purposes only and should not be used in any
> production use case. It is intended to highlight concepts of Semantic Kernel and not
> any architectural / security design practices to be used.

## Running the sample

1. You will need an [Open AI Key](https://openai.com/api/) or
   [Azure Open AI Service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart) for this sample.
2. Ensure the service API is already running `http://localhost:7071`. If not learn how to start it [here](../starter-api-azure-function/README.md).
3. **Run** the following command `yarn install` (if you have never run the sample before) and/or `yarn start` from the command line.
4. A browser will open or you can navigate to `http://localhost:3000` to use the sample.

## About the GitHub Repo Q&A Bot Sample

The GitHub Repo Q&A Bot sample allows you to pull in data from a public GitHub repo into a local memory store in order to ask questions about the project and to get answers about it.  The sample highlights how [memory](TODO Link to memory) and [embeddings](TODO Link to embeddings) work along with X SK Functions when the size of the data is larger than the allowed token limited.  Each SK function will call Open AI to perform the tasks you ask about.​

> [!CAUTION]
> Each function will call Open AI which will use tokens that you will be billed for.

## Next Steps

Create Skills and SK functions: Check out the [documentation](TODO link to documentation) for how to create Skills or watch the [video​](TODO Link to video)
Join the community: Join our [Discord community](https://aka.ms/SKDiscord) to share ideas and get help​
Contribute: We need your help to make this the best it can be.  Learn how you can [contribute](TODO Link to contribute) to this project.​
## Troubleshooting Steps