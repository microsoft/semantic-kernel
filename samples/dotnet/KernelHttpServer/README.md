# Semantic Kernel Service API (For Learning Samples)

> [!IMPORTANT]
> This sample will be removed in a future release. If you are looking for samples that demonstrate
> how to use Semantic Kernel, please refer to the sample folders in the root [python](../../../python/samples/)
> and [dotnet](../../../dotnet/samples/) folders.

Watch the [Service API Quick Start Video](https://aka.ms/SK-Local-API-Setup).

This service API is written in C# against Azure Function Runtime v4 and exposes
some Semantic Kernel APIs that you can call via HTTP POST requests for the learning samples.

![azure-function-diagram](https://user-images.githubusercontent.com/146438/222305329-0557414d-38ce-4712-a7c1-4f6c63c20320.png)

**!IMPORTANT**

> This service API is for educational purposes only and should not be used in any production use
> case. It is intended to highlight concepts of Semantic Kernel and not any architectural
> security design practices to be used.

## Prerequisites

[Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
installation is required for this service API to run locally.

## Running the service API locally

**Run** `func start --csharp` from the command line. This will run the service API locally at `http://localhost:7071`.

Two endpoints will be exposed by the service API:

- **InvokeFunction**: [POST] `http://localhost:7071/api/skills/{skillName}/invoke/{functionName}`
- **Ping**: [GET] `http://localhost:7071/api/ping`

### Working with Secrets

We need keys to work with various aspects of the project including accessing openAI models. This opens up the possibility of exposing keys in commits. There are a [couple of options](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets?view=aspnetcore-7.0&tabs=windows) to safeguard developers from exposing keys. Outside of using the dotnet's users-secrets and environment variables, we've also added \*.development.config to the .gitignore if developers want to use config files for secret storage.

## Next steps

Now that your service API is running locally,
let's try it out in a sample app so you can learn core Semantic Kernel concepts!  
The service API will need to be run or running for each sample app you want to try.

Sample app learning examples:

- [Simple chat summary](../../apps/chat-summary-webapp-react/README.md) (**Recommended**) – learn how basic
  semantic functions can be added to an app
- [Book creator](../../apps/book-creator-webapp-react/README.md) – learn how Planner and chaining of
  semantic functions can be used in your app
- [Authentication and APIs](../../apps/auth-api-webapp-react/README.md) – learn how to connect to external
  API's with authentication while using Semantic Kernel
- [GitHub Repo Q&A](../../apps//github-qna-webapp-react/README.md) – learn how Memories and Embeddings can be used in your app
