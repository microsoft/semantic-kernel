// See https://aka.ms/new-console-template for more information

using Connectors.Amazon.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

string userInput;
ChatHistory chatHistory = new ChatHistory();
do
{
    Console.Write("Enter a prompt (or 'exit' to quit): ");
    userInput = Console.ReadLine();

    if (userInput.ToLower() != "exit")
    {
        chatHistory.AddMessage(AuthorRole.User, userInput);
        Console.WriteLine($"Chat Completion Question: {userInput}");

        // var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("amazon.titan-text-premier-v1:0").Build();
        // var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("mistral.mistral-7b-instruct-v0:2").Build();
        // var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("anthropic.claude-3-sonnet-20240229-v1:0").Build();
        // var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("anthropic.claude-3-haiku-20240307-v1:0").Build();
        // var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("anthropic.claude-v2:1").Build();
        // var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("ai21.jamba-instruct-v1:0").Build();
        // var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("cohere.command-r-plus-v1:0").Build();
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("meta.llama3-8b-instruct-v1:0").Build();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(false);

        foreach (var message in result)
        {
            // chatHistory.AddMessage(AuthorRole.Assistant, message.Content); //put this in GenerateChatMessageAsync in chatClient
            Console.WriteLine($"Chat Completion Answer: {message.Content}");
            Console.WriteLine();
        }
    }
} while (userInput.ToLower() != "exit");

const string UserPrompt2 = "What is 2 + 2?";
Console.WriteLine($"Text Generation Question: {UserPrompt2}");
// var kernel2 = Kernel.CreateBuilder().AddBedrockTextGenerationService("amazon.titan-text-premier-v1:0").Build();
// var kernel2 = Kernel.CreateBuilder().AddBedrockTextGenerationService("mistral.mistral-7b-instruct-v0:2").Build();
var kernel2 = Kernel.CreateBuilder().AddBedrockTextGenerationService("ai21.jamba-instruct-v1:0").Build();

var textGenerationService = kernel2.GetRequiredService<ITextGenerationService>();
var textGeneration = await textGenerationService.GetTextContentsAsync(UserPrompt2).ConfigureAwait(false);
if (textGeneration.Count > 0)
{
    var firstTextContent = textGeneration.FirstOrDefault();
    if (firstTextContent != null)
    {
        Console.WriteLine("Text Generation Answer: " + firstTextContent.Text);
    }
    else
    {
        Console.WriteLine("Text Generation Answer: (none)");
    }
}
else
{
    Console.WriteLine("Text Generation Answer: (No output text)");
}



