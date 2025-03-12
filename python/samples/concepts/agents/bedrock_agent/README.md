# Concept samples on how to use AWS Bedrock agents

## Pre-requisites

1. You need to have an AWS account and [access to the foundation models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-permissions.html)
2. [AWS CLI installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [configured](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)

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

bedrock_agent = BedrockAgent.create_and_prepare_agent(
    name="your_agent_name",
    instructions="your_instructions",
    runtime_client=runtime_client,
    client=client,
    [...other parameters you may need...]
)
```

## Samples

| Sample | Description |
|--------|-------------|
| [bedrock_agent_simple_chat.py](bedrock_agent_simple_chat.py) | Demonstrates basic usage of the Bedrock agent. |
| [bedrock_agent_simple_chat_streaming.py](bedrock_agent_simple_chat_streaming.py) | Demonstrates basic usage of the Bedrock agent with streaming. |
| [bedrock_agent_with_kernel_function.py](bedrock_agent_with_kernel_function.py) | Shows how to use the Bedrock agent with a kernel function. |
| [bedrock_agent_with_kernel_function_streaming.py](bedrock_agent_with_kernel_function_streaming.py) | Shows how to use the Bedrock agent with a kernel function with streaming. |
| [bedrock_agent_with_code_interpreter.py](bedrock_agent_with_code_interpreter.py) | Example of using the Bedrock agent with a code interpreter. |
| [bedrock_agent_with_code_interpreter_streaming.py](bedrock_agent_with_code_interpreter_streaming.py) | Example of using the Bedrock agent with a code interpreter and streaming. |
| [bedrock_mixed_chat_agents.py](bedrock_mixed_chat_agents.py) | Example of using multiple chat agents in a single script. |
| [bedrock_mixed_chat_agents_streaming.py](bedrock_mixed_chat_agents_streaming.py) | Example of using multiple chat agents in a single script with streaming. |

## Before running the samples

You need to set up some environment variables to run the samples. Please refer to the [.env.example](.env.example) file for the required environment variables.

### `BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN`

On your AWS console, go to the IAM service and go to **Roles**. Find the role you want to use and click on it. You will find the ARN in the summary section.

### `BEDROCK_AGENT_FOUNDATION_MODEL`

You need to make sure you have permission to access the foundation model. You can find the model ID in the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html). To see the models you have access to, find the policy attached to your role you should see a list of models you have access to under the `Resource` section.

### How to add the `bedrock:InvokeModelWithResponseStream` action to an IAM policy

1. Open the [IAM console](https://console.aws.amazon.com/iam/).
2. On the left navigation pane, choose `Roles` under `Access management`.
3. Find the role you want to edit and click on it.
4. Under the `Permissions policies` tab, click on the policy you want to edit.
5. Under the `Permissions defined in this policy` section, click on the service. You should see **Bedrock** if you already have access to the Bedrock agent service.
6. Click on the service, and then click `Edit`.
7. On the right, you will be able to add an action. Find the service and search for `InvokeModelWithResponseStream`.
8. Check the box next to the action and then scroll all the way down and click `Next`.
9. Follow the prompts to save the changes.
