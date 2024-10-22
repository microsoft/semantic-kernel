# Google - Gemini

Gemini models are Google's large language models. Semantic Kernel provides two connectors to access these models from Google Cloud.

## Google AI

You can access the Gemini API from Google AI Studio. This mode of access is for quick prototyping as it relies on API keys.

Follow [these instructions](https://cloud.google.com/docs/authentication/api-keys) to create an API key.

Once you have an API key, you can start using Gemini models in SK using the `google_ai` connector. Example:

```Python
kernel = Kernel()
kernel.add_service(
    GoogleAIChatCompletion(
        gemini_model_id="gemini-1.5-flash",
        api_key="...",
    )
)
...
```

> Alternatively, you can use an .env file to store the model id and api key.

## Vertex AI

Google also offers access to Gemini through its Vertex AI platform. Vertex AI provides a more complete solution to build your enterprise AI applications end-to-end. You can read more about it [here](https://cloud.google.com/vertex-ai/generative-ai/docs/migrate/migrate-google-ai).

This mode of access requires a Google Cloud service account. Follow these [instructions](https://cloud.google.com/vertex-ai/generative-ai/docs/migrate/migrate-google-ai) to create a Google Cloud project if you don't have one already. Remember the `project id` as it is required to access the models.

Follow the steps below to set up your environment to use the Vertex AI API:

- [Install the gcloud CLI](https://cloud.google.com/sdk/docs/install)
- [Initialize the gcloud CLI](https://cloud.google.com/sdk/docs/initializing)

Once you have your project and your environment is set up, you can start using Gemini models in SK using the `vertex_ai` connector. Example:

```Python
kernel = Kernel()
kernel.add_service(
    VertexAIChatCompletion(
        project_id="...",
        gemini_model_id="gemini-1.5-flash",
    )
)
...
```

> Alternatively, you can use an .env file to store the model id and project id.

## Why is there code that looks almost identical in the implementations on the two connectors

The two connectors have very similar implementations, including the utils files. However, they are fundamentally different as they depend on different packages from Google. Although the namings of many types are identical, they are different types.