// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.TextGeneration;

namespace FunctionCalling;

/// <summary>
/// The following example shows how to use Semantic Kernel with the HuggingFace <see cref="HuggingFaceTextGenerationService"/>
/// to implement function calling with the Nexus Raven model.
/// </summary>
/// <param name="output">The test output helper.</param>
public class NexusRaven_FunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Nexus Raven endpoint
    /// </summary>
    private Uri RavenEndpoint => new("http://nexusraven.nexusflow.ai");

    /// <summary>
    /// Invokes the Nexus Raven model using Text Generation.
    /// </summary>
    [Fact]
    public async Task InvokeTextGenerationAsync()
    {
        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextGeneration(endpoint: RavenEndpoint)
            .Build();

        var textGeneration = kernel.GetRequiredService<ITextGenerationService>();
        var prompt = "What is deep learning?";

        var result = await textGeneration.GetTextContentsAsync(prompt);

        Console.WriteLine(result[0].ToString());
    }

    /// <summary>
    /// Invokes the Nexus Raven model with Function Calling.
    /// </summary>
    [Fact]
    public async Task InvokeTextGenerationWithFunctionCallingAsync()
    {
        using var handler = new LoggingHandler(new HttpClientHandler(), this.Output);
        using var httpClient = new HttpClient(handler);

        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceTextGeneration(
                endpoint: RavenEndpoint,
                httpClient: httpClient)
            .Build();
        var plugin = ImportFunctions(kernel);
        var textGeneration = kernel.GetRequiredService<ITextGenerationService>();

        // This Handlebars template is used to format the available KernelFunctions so
        // they can be understood by the NexusRaven model. The function name, signature and
        // description must be provided. NexusRaven can reason over the list of functions and
        // determine which ones need to be called for the current query.
        var template =
        """"
        {{#each (functions)}}
        Function:
        {{Name}}{{Signature}}
        """
        {{Description}}
        """
        {{/each}}

        User Query:{{prompt}}<human_end>
        """";

        var prompt = "What is the weather like in Dublin?";
        var functions = plugin.Select(f => new FunctionDefinition { Name = f.Name, Description = f.Description, Signature = CreateSignature(f) }).ToList();
        var executionSettings = new HuggingFacePromptExecutionSettings { Temperature = 0.001F, MaxNewTokens = 1024, ReturnFullText = false, DoSample = false }; // , Stop = ["<bot_end>"]
        KernelArguments arguments = new(executionSettings) { { "prompt", prompt }, { "functions", functions } };

        var factory = new HandlebarsPromptTemplateFactory();
        var promptTemplate = factory.Create(new PromptTemplateConfig(template) { TemplateFormat = "handlebars" });
        var rendered = await promptTemplate.RenderAsync(kernel, arguments);

        Console.WriteLine(" Prompt:\n====================");
        Console.WriteLine(rendered);

        var function = kernel.CreateFunctionFromPrompt(template, templateFormat: "handlebars", promptTemplateFactory: new HandlebarsPromptTemplateFactory());

        var result = await kernel.InvokeAsync(function, arguments);

        Console.WriteLine("\n Response:\n====================");
        Console.WriteLine(result.ToString());
    }

    // The signature must be Python compliant and currently only supports primitive values
    private static string CreateSignature(KernelFunction function)
    {
        var signature = new StringBuilder();
        var parameters = function.Metadata.Parameters;
        signature.Append('(');
        foreach (var parameter in parameters)
        {
            signature.Append(parameter.Name).Append(':').Append(GetType(parameter));
        }
        signature.Append(')');
        return signature.ToString();
    }

    private static string GetType(KernelParameterMetadata parameter)
    {
        if (parameter.Schema is not null)
        {
            var rootElement = parameter.Schema.RootElement;
            if (rootElement.TryGetProperty("type", out var type))
            {
                return type.GetString() ?? string.Empty;
            }
        }
        return string.Empty;
    }

    private static KernelPlugin ImportFunctions(Kernel kernel)
    {
        return kernel.ImportPluginFromFunctions("WeatherPlugin",
        [
            kernel.CreateFunctionFromMethod(
                (string cityName) => "12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy",
                "GetWeatherForCity",
                "Gets the current weather for the specified city",
                new List<KernelParameterMetadata>
                {
                    new("cityName") { Description = "The city name", ParameterType = string.Empty.GetType() }
                }),
        ]);
    }

    /// <summary>
    /// Function definition for use with Nexus Raven.
    /// </summary>
    private sealed class FunctionDefinition
    {
        public string Name { get; init; }
        public string Signature { get; init; }
        public string Description { get; init; }
    }
}
