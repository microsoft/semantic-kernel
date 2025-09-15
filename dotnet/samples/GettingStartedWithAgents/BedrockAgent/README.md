# Concept samples on how to use AWS Bedrock agents

## Pre-requisites

1. You need to have an AWS account and [access to the foundation models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-permissions.html)
2. [AWS CLI installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [configured](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)

## Before running the samples

You need to set up some user secrets to run the samples.

### `BedrockAgent:AgentResourceRoleArn`

On your AWS console, go to the IAM service and go to **Roles**. Find the role you want to use and click on it. You will find the ARN in the summary section.

```
dotnet user-secrets set "BedrockAgent:AgentResourceRoleArn" "arn:aws:iam::...:role/..."
```

### `BedrockAgent:FoundationModel`

You need to make sure you have permission to access the foundation model. You can find the model ID in the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html). To see the models you have access to, find the policy attached to your role you should see a list of models you have access to under the `Resource` section.

```
dotnet user-secrets set "BedrockAgent:FoundationModel" "..."
```

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
