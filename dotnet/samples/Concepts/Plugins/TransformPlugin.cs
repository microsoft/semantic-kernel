// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Plugins;

/// <summary>
/// Sample showing how to transform a <see cref="KernelPlugin"/> so that not all parameters are advertised to the LLM
/// and instead the argument values are provided by the client code.
/// </summary>
public sealed class TransformPlugin(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// A plugin that returns favorite information for a user.
    /// </summary>
    public class UserFavorites
    {
        [KernelFunction]
        [Description("Returns the favorite color for the user.")]
        public string GetFavoriteColor([Description("Email address of the user.")] string email)
        {
            return email.Equals("bob@contoso.com", StringComparison.OrdinalIgnoreCase) ? "Green" : "Blue";
        }

        [KernelFunction]
        [Description("Returns the favorite animal of the specified type for the user.")]
        public string GetFavoriteAnimal([Description("Email address of the user.")] string email, [Description("Type of animal.")] AnimalType animalType)
        {
            if (email.Equals("bob@contoso.com", StringComparison.OrdinalIgnoreCase))
            {
                return GetBobsFavoriteAnimal(animalType);
            }

            return GetDefaultFavoriteAnimal(animalType);
        }

        private string GetBobsFavoriteAnimal(AnimalType animalType) => animalType switch
        {
            AnimalType.Mammals => "Dog",
            AnimalType.Birds => "Sparrow",
            AnimalType.Reptiles => "Lizard",
            AnimalType.Amphibians => "Salamander",
            AnimalType.Fish => "Tuna",
            AnimalType.Invertebrates => "Spider",
            _ => throw new ArgumentOutOfRangeException(nameof(animalType), $"Unexpected animal type: {animalType}"),
        };

        private string GetDefaultFavoriteAnimal(AnimalType animalType) => animalType switch
        {
            AnimalType.Mammals => "Horse",
            AnimalType.Birds => "Eagle",
            AnimalType.Reptiles => "Snake",
            AnimalType.Amphibians => "Frog",
            AnimalType.Fish => "Shark",
            AnimalType.Invertebrates => "Ant",
            _ => throw new ArgumentOutOfRangeException(nameof(animalType), $"Unexpected animal type: {animalType}"),
        };
    }

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum AnimalType
    {
        [Description("These warm-blooded animals have hair or fur, give birth to live young, and produce milk to feed their offspring. Examples include dogs, tigers, and elephants.")]
        Mammals,
        [Description("Feathered creatures that lay eggs and have beaks, wings, and hollow bones. They are adapted for flight and include species like eagles and sparrows.")]
        Birds,
        [Description("Cold-blooded animals with scales, lay eggs, and often live on land. Snakes, lizards, and turtles fall into this category.")]
        Reptiles,
        [Description("These animals can live both in water and on land. They typically start life as aquatic larvae (like tadpoles) and later transform into adults.Frogs and salamanders are examples.")]
        Amphibians,
        [Description("Aquatic vertebrates that breathe through gills and have scales.They come in various shapes and sizes, from tiny minnows to massive sharks.")]
        Fish,
        [Description("The most diverse group, lacking backbones. Insects (like ants and butterflies) and arachnids (such as spiders) are common examples.")]
        Invertebrates
    }

    /// <summary>
    /// Shows how LLM will respond if the prompt is missing information required to call a function.
    /// </summary>
    [Fact]
    public async Task MissingRequiredInformationAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        kernelBuilder.Plugins.AddFromType<UserFavorites>();
        Kernel kernel = kernelBuilder.Build();

        // Invoke the kernel with a prompt and allow the AI to automatically invoke functions
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine(await kernel.InvokePromptAsync("What color should I paint the fence?", new(settings)));
        Console.WriteLine(await kernel.InvokePromptAsync("I am going diving what animals would I like to see?", new(settings)));

        // Example responses
        // If you would like a suggestion based on your preferences, I can find out your favorite color if you provide your email address.
        // To help you with that, I would need to know your favorite type of aquatic animals.If you provide your email, I can check your preferences, if available, for your favorite type of fish or other marine creatures.
    }

    /// <summary>
    /// Shows how to transform a plugin so that certain parameters are removed and the arguments are provided separately.
    /// </summary>
    [Fact]
    public async Task CreatePluginWithAlteredParametersAsync()
    {
        // Create a new Plugin which hides parameters that require PII
        var plugin = KernelPluginFactory.CreateFromType<UserFavorites>();
        var transformedPlugin = CreatePluginWithParameters(
        plugin,
        (KernelParameterMetadata parameter) => parameter.Name != "email",
            (KernelFunctionMetadata function, KernelArguments arguments) => arguments.Add("email", "bob@contoso.com"));

        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        kernelBuilder.Plugins.Add(transformedPlugin);
        Kernel kernel = kernelBuilder.Build();

        // Invoke the kernel with a prompt and allow the AI to automatically invoke functions
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        Console.WriteLine(await kernel.InvokePromptAsync("What color should my new car be?", new(settings)));
        Console.WriteLine(await kernel.InvokePromptAsync("What color should I paint the fence?", new(settings)));
        Console.WriteLine(await kernel.InvokePromptAsync("What is my favorite cold-blooded animal?", new(settings)));
        Console.WriteLine(await kernel.InvokePromptAsync("What is my favorite marine animal?", new(settings)));
        Console.WriteLine(await kernel.InvokePromptAsync("What is my favorite creepy crawly?", new(settings)));
        Console.WriteLine(await kernel.InvokePromptAsync("What is my favorite four legged friend?", new(settings)));
        Console.WriteLine(await kernel.InvokePromptAsync("I am going diving what animals would I like to see?", new(settings)));

        // Example response
        // Your favorite color is Green. 🌿
        // Your favorite cold-blooded animal is a lizard.
        // Your favorite marine animal is the Tuna. 🐟
        // Your favorite creepy crawly is a spider! 🕷️
    }

    public delegate bool IncludeKernelParameter(KernelParameterMetadata parameter);

    public delegate void UpdateKernelArguments(KernelFunctionMetadata function, KernelArguments arguments);

    /// <summary>
    /// Create a <see cref="KernelPlugin"/> instance from the provided instance where each function only includes
    /// permitted parameters. The <see cref="IncludeKernelParameter"/> delegate is called to determine whether or not
    /// parameter will be included. The <see cref="UpdateKernelArguments"/> delegate is called to update the arguments
    /// and allow additional values to be included.
    /// </summary>
    public static KernelPlugin CreatePluginWithParameters(KernelPlugin plugin, IncludeKernelParameter includeKernelParameter, UpdateKernelArguments updateKernelArguments)
    {
        List<KernelFunction>? functions = [];

        foreach (KernelFunction function in plugin)
        {
            functions.Add(CreateFunctionWithParameters(function, includeKernelParameter, updateKernelArguments));
        }

        return KernelPluginFactory.CreateFromFunctions(plugin.Name, plugin.Description, functions);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> instance from the provided instance which only includes permitted parameters.
    /// The function method will add additional argument values before calling the original function.
    /// </summary>
    private static KernelFunction CreateFunctionWithParameters(KernelFunction function, IncludeKernelParameter includeKernelParameter, UpdateKernelArguments updateKernelArguments)
    {
        var method = (Kernel kernel, KernelFunction currentFunction, KernelArguments arguments, CancellationToken cancellationToken) =>
        {
            updateKernelArguments(currentFunction.Metadata, arguments);
            return function.InvokeAsync(kernel, arguments, cancellationToken);
        };

        var options = new KernelFunctionFromMethodOptions()
        {
            FunctionName = function.Name,
            Description = function.Description,
            Parameters = CreateParameterMetadataWithParameters(function.Metadata.Parameters, includeKernelParameter),
            ReturnParameter = function.Metadata.ReturnParameter,
        };

        return KernelFunctionFactory.CreateFromMethod(method, options);
    }

    /// <summary>
    /// Create a list of KernelParameterMetadata instances from the provided instances which only includes permitted parameters.
    /// </summary>
    private static List<KernelParameterMetadata> CreateParameterMetadataWithParameters(IReadOnlyList<KernelParameterMetadata> parameters, IncludeKernelParameter includeKernelParameter)
    {
        List<KernelParameterMetadata>? parametersToInclude = [];
        foreach (var parameter in parameters)
        {
            if (includeKernelParameter(parameter))
            {
                parametersToInclude.Add(parameter);
            }
        }
        return parametersToInclude;
    }
}
