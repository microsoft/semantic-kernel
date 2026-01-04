using System;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.Anthropic;

var settings = new AnthropicPromptExecutionSettings { Temperature = 0.7 };
var json = JsonSerializer.Serialize(settings);
Console.WriteLine(\"JSON: \" + json);
