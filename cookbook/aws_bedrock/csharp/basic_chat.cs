using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.Bedrock;
using Microsoft.Extensions.Configuration;

public class BedrockChatExample
{
    private readonly IKernel _kernel;
    private readonly string _modelId;

    public BedrockChatExample(IConfiguration configuration)
    {
        // Load configuration
        _modelId = configuration["AWSBedrockSettings:ModelId"] ?? "anthropic.claude-v2";

        // Initialize the kernel with AWS Bedrock
        _kernel = Kernel.Builder
            .WithAWSBedrockChatCompletion(_modelId)
            .Build();
    }

    public async Task RunChatExampleAsync()
    {
        Console.WriteLine("Starting chat with AWS Bedrock...\n");

        // Create a chat history
        var chatHistory = new ChatHistory();

        while (true)
        {
            Console.Write("User: ");
            var userInput = Console.ReadLine();

            if (string.IsNullOrEmpty(userInput) || userInput.ToLower() == "exit")
            {
                break;
            }

            // Add user message to history
            chatHistory.AddUserMessage(userInput);

            try
            {
                // Get chat completion
                var response = await _kernel.GetRequiredService<IChatCompletion>()
                    .GetChatMessageContentAsync(chatHistory);

                // Add assistant response to history
                chatHistory.AddAssistantMessage(response.Content);

                Console.WriteLine($"Assistant: {response.Content}\n");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
                break;
            }
        }
    }

    public static async Task Main()
    {
        // Load configuration
        IConfiguration configuration = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("appsettings.json", optional: false)
            .Build();

        var example = new BedrockChatExample(configuration);
        await example.RunChatExampleAsync();
    }
}