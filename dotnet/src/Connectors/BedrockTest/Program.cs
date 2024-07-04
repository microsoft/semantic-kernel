// See https://aka.ms/new-console-template for more information

using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

const string userPrompt = "What is the color of the sky?";
Console.WriteLine($"Question: {userPrompt}");

var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("amazon.titan-text-premier-v1:0").Build();
var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
var chatHistory = new ChatHistory(userPrompt);
var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(false);
foreach (var message in result)
{
    Console.WriteLine($"Chat Completion Answer: {message.Content}");
    Console.WriteLine();
}

var kernel2 = Kernel.CreateBuilder().AddBedrockTextGenerationService("amazon.titan-text-premier-v1:0").Build();
var textGenerationService = kernel2.GetRequiredService<ITextGenerationService>();
var textGeneration = await textGenerationService.GetTextContentsAsync(userPrompt).ConfigureAwait(false);
Console.WriteLine($"Text Generation Answer: {textGeneration[0]}");



