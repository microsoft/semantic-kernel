# Semantic Kernel - Amazon Bedrock Models Demo

This program demonstrates how to use the Semantic Kernel using the AWS SDK for .NET with Amazon Bedrock Runtime to 
perform various tasks, such as chat completion, text generation, and the streaming versions of these services. The
BedrockRuntime is a managed service provided by AWS that simplifies the deployment and management of large language
models (LLMs).

## Authentication

The AWS setup library automatically authenticates with the BedrockRuntime using the AWS credentials configured 
on your machine or in the environment.

### Setup AWS Credentials

If you don't have any credentials configured, you can easily setup in your local machine using the [AWS CLI tool](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) following the commands below after installation

```powershell
> aws configure 
AWS Access Key ID [None]: Your-Access-Key-Here
AWS Secret Access Key [None]: Your-Secret-Access-Key-Here
Default region name [None]: us-east-1 (or any other)
Default output format [None]: json
```

With this property configured you can run the application and it will automatically authenticate with the AWS SDK.

## Features

This demo program allows you to do any of the following:
- Perform chat completion with a selected Bedrock foundation model. 
- Perform text generation with a selected Bedrock foundation model. 
- Perform streaming chat completion with a selected Bedrock foundation model. 
- Perform streaming text generation with a selected Bedrock foundation model.

## Usage

1. Run the application.
2. Choose a service option from the menu (1-4). 
   - For chat completion and streaming chat completion, enter a prompt and continue with the conversation.
   - For text generation and streaming text generation, enter a prompt and view the generated text.
3. To exit chat completion or streaming chat completion, leave the prompt empty.
   - The available models for each task are listed before you make your selection. Note that some models do not support
   certain tasks, and they are skipped during the selection process.