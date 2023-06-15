# Semantic Kernel Service API (For Learning Samples)

Watch the [Service API Quick Start Video](https://aka.ms/SK-Local-API-Setup).

This service API is written in Python against Azure Function Runtime v4 and exposes
some Semantic Kernel APIs that you can call via HTTP POST requests for the learning samples.

![azure-function-diagram](https://user-images.githubusercontent.com/146438/222305329-0557414d-38ce-4712-a7c1-4f6c63c20320.png)

## !IMPORTANT

> This service API is for educational purposes only and should not be used in any production use
> case. It is intended to highlight concepts of Semantic Kernel and not any architectural
> security design practices to be used.

## Prerequisites

[Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
installation is required for this service API to run locally.

## Configuring the host

This starter can be configured in two ways:

- A `.env` file in the project which holds api keys and other secrets and configurations
- Or with HTTP Headers on each request

Make sure you have an
[Open AI API Key](https://openai.com/api/) or
[Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)

### Configure with a .env file

Copy the `.env.example` file to a new file named `.env`. Then, copy those keys into the `.env` file:

```
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_DEPLOYMENT_NAME=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
```

### Configure with HTTP Headers

On each HTTP request, use these headers:

```
"x-ms-sk-completion-model" # e.g. text-davinci-003
"x-ms-sk-completion-endpoint" # e.g. https://my-endpoint.openai.azure.com
"x-ms-sk-completion-backend" # AZURE_OPENAI or OPENAI
"x-ms-sk-completion-key" # Your API key
```

## Running the service API locally

**Run** `python -m venv .venv && .\.venv\Scripts\python -m pip install -r requirements.txt && .venv\Scripts\activate`
to create and activate a virtual environment
**Run** `func start` from the command line. This will run the service API locally at `http://localhost:7071`.

Four endpoints will be exposed by the service API:

- **InvokeFunction**: [POST] `http://localhost:7071/api/skills/{skillName}/invoke/{functionName}`
- **Ping**: [GET] `http://localhost:7071/api/ping`
- **CreatePlan**: [POST] `http://localhost:7071/api/planner/createplan`
- **ExecutePlan**: [POST] `http://localhost:7071/api/planner/executeplan/{maxSteps}`

They accept input in the JSON body of the request:

```json
{
  "value": "", // the "input" of the prompt
  "inputs": // a list of extra key-value parameters for ContextVariables or Plan State
  [
    {"key": "", "value": ""}
  ],
  "skills": [] // list of skills to use (for the planner)
}
```

For planning, first create a plan with your prompt in the "value" parameter.  Take the JSON "state" response,
rename "state" to "inputs", and use it for the input to ExecutePlan.

## Next steps

Now that your service API is running locally,
let's try it out in a sample app so you can learn core Semantic Kernel concepts!  
The service API will need to be run or running for each sample app you want to try.

Sample app learning examples:

- [Book creator](../../apps/book-creator-webapp-react/README.md) – learn how Planner and chaining of
    semantic functions can be used in your app
