# AWS Bedrock Cookbook for Semantic Kernel

This cookbook demonstrates how to use AWS Bedrock with Semantic Kernel for various AI scenarios. AWS Bedrock provides access to high-quality foundation models like Claude (Anthropic), Llama 2 (Meta), and others through a unified API.

## Prerequisites

- An AWS account with access to AWS Bedrock
- AWS credentials configured locally
- .NET 6.0 or later
- Semantic Kernel SDK

## Examples

1. **Basic Chat (basic_chat.cs)**

   - Simple chatbot implementation using Claude model
   - Demonstrates basic conversation handling

2. **Function Calling (function_calling.cs)**

   - Shows how to use function calling capabilities
   - Includes examples of native functions and semantic functions

3. **RAG Pattern (rag_example.cs)**
   - Retrieval Augmented Generation implementation
   - Uses Amazon OpenSearch for document storage
   - Shows embedding generation and semantic search

## Configuration

Before running the examples, make sure to:

1. Configure your AWS credentials
2. Set up the necessary AWS Bedrock model access
3. Update the configuration in `appsettings.json` with your AWS settings

## Running the Examples

Each example can be run independently. Follow the instructions in each file's header for specific setup and execution details.

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock)
- [Semantic Kernel Documentation](https://learn.microsoft.com/semantic-kernel)
- [AWS SDK for .NET](https://aws.amazon.com/sdk-for-net/)
