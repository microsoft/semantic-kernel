# Amazon - Bedrock

[Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html) is a service provided by Amazon Web Services (AWS) that allows you to access large language models with a serverless experience. Semantic Kernel provides a connector to access these models from AWS.

## Prerequisites

- An AWS account and [access to the foundation models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-permissions.html)
- [AWS CLI installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [configured](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)

### Configuration

Follow this [guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration) to configure your environment to use the Bedrock API.

Please configure the `aws_access_key_id`, `aws_secret_access_key`, and `region` otherwise you will need to create custom clients for the services. For example:

```python
runtime_client=boto.client(
    "bedrock-runtime",
    aws_access_key_id="your_access_key",
    aws_secret_access_key="your_secret_key",
    region_name="your_region",
    [...other parameters you may need...]
)
client=boto.client(
    "bedrock",
    aws_access_key_id="your_access_key",
    aws_secret_access_key="your_secret_key",
    region_name="your_region",
    [...other parameters you may need...]
)

bedrock_chat_completion_service = BedrockChatCompletion(runtime_client=runtime_client, client=client)
```

## Supports

### Region

To find model supports by AWS regions, refer to this [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/models-regions.html).

### Input & Output Modalities

Foundational models in Bedrock support the multiple modalities, including text, image, and embedding. However, not all models support the same modalities. Refer to the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html) for more information.

The Bedrock connector supports all modalities except for **image embeddings, and text to image**.

### Text completion vs chat completion

Some models in Bedrock supports only text completion, or only chat completion (aka Converse API), or both. Refer to the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/models-features.html) for more information.

### Tool Use

Not all models in Bedrock support tools. Refer to the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/models-features.html) for more information.

### Streaming vs Non-Streaming

Not all models in Bedrock support streaming. You can use the boto3 client to check if a model supports streaming. Refer to the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html) and the [Boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock/client/get_foundation_model.html) for more information.

You can also directly call the `get_foundation_model_info("model_id")` method from the Bedrock connector to check if a model supports streaming.

> Note: The bedrock connector will check if a model supports streaming before making a streaming request to the model.

## Model specific parameters

Foundation models can have specific parameters that are unique to the model or the model provider. You can refer to this [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html) for more information.

You can pass these parameters via the `extension_data` field in the `PromptExecutionSettings` object.

## Unsupported features

- [Guardrail](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)