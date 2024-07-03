// See https://aka.ms/new-console-template for more information

using Connectors.Amazon.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;

var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("amazon.titan-text-premier-v1:0").Build();

const string userPrompt = "Who are you?";
Console.WriteLine($"Question: {userPrompt}");

var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
var chatHistory = new ChatHistory(userPrompt);
var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(false);
Console.WriteLine($"Answer: {result[0]}");



