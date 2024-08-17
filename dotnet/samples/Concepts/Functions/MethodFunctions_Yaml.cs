// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.SemanticKernel;

namespace Functions;

public class MethodFunctions_Yaml(ITestOutputHelper output) : BaseTest(output)
{
    private const string FunctionConfig = """
        name: ValidateTaskId
        description: Validate a task id.
        input_variables:
          - name: kernel
            description: Kernel instance.
          - name: taskId
            description: Task identifier.
            is_required: true
        output_variable:
          description: String indicating whether or not the task id is valid.
        """;

    /// <summary>
    /// This example create a plugin and uses a separate configuration file for the function metadata.
    /// </summary>
    /// <remarks>
    /// Some reasons you would want to do this:
    /// 1. It's not possible to modify the existing code to add the KernelFunction attribute.
    /// 2. You want to keep the function metadata separate from the function implementation.
    /// </remarks>
    [Fact]
    public async Task CreateFunctionFromMethodWithYamlConfigAsync()
    {
        var kernel = new Kernel();

        var config = KernelFunctionYaml.ToPromptTemplateConfig(FunctionConfig);

        var target = new ValidatorPlugin();
        MethodInfo method = target.GetType().GetMethod(config.Name!)!;
        var functions = new List<KernelFunction>();
        var functionName = config.Name;
        var description = config.Description;
        var parameters = config.InputVariables;
        functions.Add(KernelFunctionFactory.CreateFromMethod(method, target, new()
        {
            FunctionName = functionName,
            Description = description,
            Parameters = parameters.Select(p => new KernelParameterMetadata(p.Name) { Description = p.Description, IsRequired = p.IsRequired }).ToList(),
        }));

        var plugin = kernel.ImportPluginFromFunctions("ValidatorPlugin", functions);

        var function = plugin["ValidateTaskId"];
        var result = await kernel.InvokeAsync(function, new() { { "taskId", "1234" } });
        Console.WriteLine(result.GetValue<string>());

        Console.WriteLine("Function Metadata:");
        Console.WriteLine(function.Metadata.Description);
        Console.WriteLine(function.Metadata.Parameters[0].Description);
        Console.WriteLine(function.Metadata.Parameters[1].Description);
    }

    /// <summary>
    /// Plugin example with no KernelFunction or Description attributes.
    /// </summary>
    private sealed class ValidatorPlugin
    {
        public string ValidateTaskId(Kernel kernel, string taskId)
        {
            return taskId.Equals("1234", StringComparison.Ordinal) ? "Valid task id" : "Invalid task id";
        }
    }
}
