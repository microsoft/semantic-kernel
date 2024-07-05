// See https://aka.ms/new-console-template for more information

using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

const string UserPrompt = "What is the color of the sky?";
Console.WriteLine($"Chat Completion Question: {UserPrompt}");

var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("amazon.titan-text-premier-v1:0").Build();
var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
var chatHistory = new ChatHistory(UserPrompt);
var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(false);
foreach (var message in result)
{
    Console.WriteLine($"Chat Completion Answer: {message.Content}");
    Console.WriteLine();
}

const string UserPrompt2 = "What is the color of the grass?";
Console.WriteLine($"Text Generation Question: {UserPrompt2}");
var kernel2 = Kernel.CreateBuilder().AddBedrockTextGenerationService("amazon.titan-text-premier-v1:0").Build();
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



