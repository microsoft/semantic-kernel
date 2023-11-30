// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading;
using HandlebarsDotNet;
using HandlebarsDotNet.Compiler;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Provides extension methods for rendering Handlebars templates in the context of a Semantic Kernel.
/// </summary>
internal sealed class HandlebarsTemplateEngineExtensions
{
    /// <summary>
    /// The character used to delimit the plugin name and function name in a Handlebars template.
    /// </summary>
    public const string ReservedNameDelimiter = "-";

    /// <summary>
    /// Renders a Handlebars template in the context of a Semantic Kernel.
    /// </summary>
    /// <param name="kernel">The Semantic Kernel.</param>
    /// <param name="template">The Handlebars template to render.</param>
    /// <param name="arguments">The dictionary of arguments to pass to the Handlebars template engine.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The rendered Handlebars template.</returns>
    public static string Render(
        Kernel kernel,
        string template,
        Dictionary<string, object?> arguments,
        CancellationToken cancellationToken = default)
    {
        IHandlebars handlebarsInstance = HandlebarsDotNet.Handlebars.Create(
            new HandlebarsConfiguration
            {
                NoEscape = true
            });

        var state = new KernelArguments();

        // Add helpers for each function
        foreach (KernelFunctionMetadata function in kernel.Plugins.GetFunctionsMetadata())
        {
            RegisterFunctionAsHelper(kernel, state, handlebarsInstance, function, arguments, cancellationToken);
        }

        // Add system helpers
        RegisterSystemHelpers(handlebarsInstance, arguments);

        var compiledTemplate = handlebarsInstance.Compile(template);
        return compiledTemplate(arguments);
    }

    private static void RegisterFunctionAsHelper(
        Kernel kernel,
        KernelArguments state,
        IHandlebars handlebarsInstance,
        KernelFunctionMetadata functionMetadata,
        Dictionary<string, object?> arguments,
        CancellationToken cancellationToken = default)
    {
        string fullyResolvedFunctionName = functionMetadata.PluginName + ReservedNameDelimiter + functionMetadata.Name;

        handlebarsInstance.RegisterHelper(fullyResolvedFunctionName, (in HelperOptions options, in Context context, in Arguments localArguments) =>
        {
            // Get the parameters from the template arguments
            if (localArguments.Any())
            {
                if (localArguments[0].GetType() == typeof(HashParameterDictionary))
                {
                    ProcessHashArguments(functionMetadata, arguments, localArguments[0] as IDictionary<string, object>);
                }
                else
                {
                    ProcessPositionalArguments(functionMetadata, arguments, localArguments);
                }
            }
            else if (functionMetadata.Parameters.Any(p => p.IsRequired))
            {
                throw new KernelException($"Invalid parameter count for function {functionMetadata.Name}. {localArguments.Length} were specified but {functionMetadata.Parameters.Count} are required.");
            }

            InitializeState(arguments, state);
            KernelFunction function = kernel.Plugins.GetFunction(functionMetadata.PluginName, functionMetadata.Name);

            // Invoke the function and write the result to the template
            return InvokeSKFunction(kernel, function, state, cancellationToken);
        });
    }

    private static void RegisterSystemHelpers(
        IHandlebars handlebarsInstance,
        Dictionary<string, object?> variables
    )
    {
        // Not exposed as a helper to the model, used for initial prompt rendering only.
        handlebarsInstance.RegisterHelper("or", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            var isAtLeastOneTruthy = false;
            foreach (var arg in arguments)
            {
                if (arg is not null)
                {
                    isAtLeastOneTruthy = true;
                }
            }

            return isAtLeastOneTruthy;
        });

        handlebarsInstance.RegisterHelper("getSchemaTypeName", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            KernelParameterMetadata parameter = (KernelParameterMetadata)arguments[0];
            return parameter.GetSchemaTypeName();
        });

        handlebarsInstance.RegisterHelper("getSchemaReturnTypeName", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            KernelReturnParameterMetadata parameter = (KernelReturnParameterMetadata)arguments[0];
            var functionName = arguments[1].ToString();
            return parameter.ToSKParameterMetadata(functionName).GetSchemaTypeName();
        });

        handlebarsInstance.RegisterHelper("array", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            // Convert all the arguments to an array
            var array = arguments.Select(a => a).ToList();

            return array;
        });

        handlebarsInstance.RegisterHelper("range", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            var start = int.Parse(arguments[0].ToString(), CultureInfo.InvariantCulture);
            var end = int.Parse(arguments[1].ToString(), CultureInfo.InvariantCulture) + 1;

            var count = end - start;

            // Create array from start to end
            var array = Enumerable.Range(start, count).ToList();

            return array;
        });

        handlebarsInstance.RegisterHelper("concat", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            List<string?> strings = arguments.Select((var) =>
            {
                if (var == null)
                {
                    return null;
                }
                return var!.ToString();
            }).ToList();
            return string.Concat(strings);
        });

        handlebarsInstance.RegisterHelper("add", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            double left = CastToNumber(arguments[0]);
            double right = CastToNumber(arguments[1]);

            return left + right;
        });

        handlebarsInstance.RegisterHelper("subtract", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            double left = CastToNumber(arguments[0]);
            double right = CastToNumber(arguments[1]);

            return right - left;
        });

        handlebarsInstance.RegisterHelper("equal", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            object? left = arguments[0];
            object? right = arguments[1];

            return left == right || (left is not null && left.Equals(right));
        });

        handlebarsInstance.RegisterHelper("lessThan", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            double left = CastToNumber(arguments[0]);
            double right = CastToNumber(arguments[1]);

            return left < right;
        });

        handlebarsInstance.RegisterHelper("greaterThan", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            double left = CastToNumber(arguments[0]);
            double right = CastToNumber(arguments[1]);

            return left > right;
        });

        handlebarsInstance.RegisterHelper("lessThanOrEqual", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            double left = CastToNumber(arguments[0]);
            double right = CastToNumber(arguments[1]);

            return left <= right;
        });

        handlebarsInstance.RegisterHelper("greaterThanOrEqual", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            double left = CastToNumber(arguments[0]);
            double right = CastToNumber(arguments[1]);

            return left >= right;
        });

        handlebarsInstance.RegisterHelper("json", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            object objectToSerialize = arguments[0];
            string json = objectToSerialize.GetType() == typeof(string) ? (string)objectToSerialize : JsonSerializer.Serialize(objectToSerialize);

            return json;
        });

        handlebarsInstance.RegisterHelper("message", (writer, options, context, arguments) =>
        {
            var parameters = arguments[0] as IDictionary<string, object>;

            // Verify that the message has a role
            if (!parameters!.ContainsKey("role"))
            {
                throw new KernelException("Message must have a role.");
            }

            writer.Write($"<{parameters["role"]}~>", false);
            options.Template(writer, context);
            writer.Write($"</{parameters["role"]}~>", false);
        });

        handlebarsInstance.RegisterHelper("raw", (writer, options, context, arguments) =>
        {
            options.Template(writer, null);
        });

        handlebarsInstance.RegisterHelper("doubleOpen", (writer, context, arguments) =>
        {
            writer.Write("{{");
        });

        handlebarsInstance.RegisterHelper("doubleClose", (writer, context, arguments) =>
        {
            writer.Write("}}");
        });

        handlebarsInstance.RegisterHelper("set", (writer, context, arguments) =>
        {
            var name = string.Empty;
            object value = string.Empty;
            if (arguments[0].GetType() == typeof(HashParameterDictionary))
            {
                // Get the parameters from the template arguments
                var parameters = arguments[0] as IDictionary<string, object>;
                name = (string)parameters!["name"];
                value = parameters!["value"];
            }
            else
            {
                name = arguments[0].ToString();
                value = arguments[1];
            }

            if (variables.TryGetValue(name, out var argVal))
            {
                variables[name] = value;
            }
            else
            {
                variables.Add(name, value);
            }
        });

        handlebarsInstance.RegisterHelper("get", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            if (arguments[0].GetType() == typeof(HashParameterDictionary))
            {
                var parameters = arguments[0] as IDictionary<string, object>;
                return variables[(string)parameters!["name"]];
            }

            return variables[arguments[0].ToString()];
        });
    }

    private static bool IsNumericType(Type? type) =>
        type is not null &&
        Type.GetTypeCode(type) is
            TypeCode.SByte or TypeCode.Int16 or TypeCode.Int32 or TypeCode.Int64 or
            TypeCode.Byte or TypeCode.UInt16 or TypeCode.UInt32 or TypeCode.UInt64 or
            TypeCode.Double or TypeCode.Single or
            TypeCode.Decimal;

    private static bool TryParseAnyNumber(string? input) =>
        // Check if input can be parsed as any of these numeric types.
        // We only need to check the largest types, as if they fail, the smaller types will also fail.
        long.TryParse(input, out _) ||
        ulong.TryParse(input, out _) ||
        double.TryParse(input, out _) ||
        decimal.TryParse(input, out _);

    private static double CastToNumber(object number)
    {
        try
        {
            return Convert.ToDouble(number, CultureInfo.CurrentCulture);
        }
        catch (FormatException)
        {
            return Convert.ToDouble(number, CultureInfo.InvariantCulture);
        }
    }

    /// <summary>
    /// Checks if handlebars argument is a valid type for the function parameter.
    /// Must satisfy one of the following:
    /// Types are an exact match.
    /// Handlebar argument is any kind of numeric type if function parameter requires a numeric type.
    /// Handlebar argument type is an object (this covers complex types).
    /// Function parameter is a generic type.
    /// </summary>
    /// <param name="parameterType">Function parameter type</param>
    /// <param name="argument">Handlebar argument </param>
    private static bool IsExpectedParameterType(KernelParameterMetadata parameterType, object argument)
    {
        if (parameterType.ParameterType == argument.GetType() ||
            argument.GetType() == typeof(object))
        {
            return true;
        }

        bool parameterIsNumeric =
            (parameterType.Schema?.RootElement.TryGetProperty("type", out JsonElement typeProperty) == true && typeProperty.GetString() == "number") ||
            IsNumericType(parameterType.ParameterType);

        return
            parameterIsNumeric &&
            (IsNumericType(argument?.GetType()) || TryParseAnyNumber(argument?.ToString()));
    }

    /// <summary>
    /// Processes the hash arguments passed to a Handlebars helper function.
    /// </summary>
    /// <param name="functionMetadata">KernelFunctionMetadata for the function being invoked.</param>
    /// <param name="variables">Dictionary of variables passed to the Handlebars template engine.</param>
    /// <param name="handlebarArgs">Dictionary of arguments passed to the Handlebars helper function.</param>
    /// <exception cref="KernelException">Thrown when a required parameter is missing.</exception>
    private static void ProcessHashArguments(KernelFunctionMetadata functionMetadata, Dictionary<string, object?> variables, IDictionary<string, object>? handlebarArgs)
    {
        // Prepare the input parameters for the function
        foreach (var param in functionMetadata.Parameters)
        {
            var fullyQualifiedParamName = functionMetadata.Name + ReservedNameDelimiter + param.Name;
            var value = handlebarArgs is not null && (handlebarArgs.TryGetValue(param.Name, out var val) || handlebarArgs.TryGetValue(fullyQualifiedParamName, out val)) ? val : null;

            if (value is not null && (handlebarArgs?.ContainsKey(param.Name) == true || handlebarArgs?.ContainsKey(fullyQualifiedParamName) == true))
            {
                variables[param.Name] = value;
            }
            else if (param.IsRequired)
            {
                throw new KernelException($"Parameter {param.Name} is required for function {functionMetadata.Name}.");
            }
        }
    }

    /// <summary>
    /// Processes the positional arguments passed to a Handlebars helper function.
    /// </summary>
    /// <param name="functionMetadata">KernelFunctionMetadata for the function being invoked.</param>
    /// <param name="variables">Dictionary of variables passed to the Handlebars template engine.</param>
    /// <param name="handlebarArgs">Dictionary of arguments passed to the Handlebars helper function.</param>
    /// <exception cref="KernelException">Thrown when a required parameter is missing.</exception>
    private static void ProcessPositionalArguments(KernelFunctionMetadata functionMetadata, Dictionary<string, object?> variables, Arguments handlebarArgs)
    {
        var requiredParameters = functionMetadata.Parameters.Where(p => p.IsRequired).ToList();
        if (handlebarArgs.Length >= requiredParameters.Count && handlebarArgs.Length <= functionMetadata.Parameters.Count)
        {
            var argIndex = 0;
            foreach (var arg in handlebarArgs)
            {
                var param = functionMetadata.Parameters[argIndex];
                if (IsExpectedParameterType(param, arg))
                {
                    variables[param.Name] = handlebarArgs[argIndex];
                    argIndex++;
                }
                else
                {
                    throw new KernelException($"Invalid parameter type for function {functionMetadata.Name}. Parameter {param.Name} expects type {param.ParameterType ?? (object?)param.Schema} but received {handlebarArgs[argIndex].GetType()}.");
                }
            }
        }
        else
        {
            throw new KernelException($"Invalid parameter count for function {functionMetadata.Name}. {handlebarArgs.Length} were specified but {functionMetadata.Parameters.Count} are required.");
        }
    }

    /// <summary>
    /// Initializes the variables in the SK function context with the variables maintained by the Handlebars template engine.
    /// </summary>
    /// <param name="variables">Dictionary of variables passed to the Handlebars template engine.</param>
    /// <param name="state">The execution state.</param>
    private static void InitializeState(Dictionary<string, object?> variables, KernelArguments state)
    {
        foreach (var v in variables)
        {
            var value = v.Value ?? "";
            var varString = !KernelParameterMetadataExtensions.IsPrimitiveOrStringType(value.GetType()) ? JsonSerializer.Serialize(value) : value.ToString();
            if (state.ContainsKey(v.Key))
            {
                state[v.Key] = varString;
            }
            else
            {
                state.Add(v.Key, varString);
            }
        }
    }

    /// <summary>
    /// Invokes an SK function and returns a typed result, if specified.
    /// </summary>
    private static object? InvokeSKFunction(
        Kernel kernel,
        KernelFunction function,
        KernelArguments state,
        CancellationToken cancellationToken = default)
    {
#pragma warning disable VSTHRD002 // Avoid problematic synchronous waits
        FunctionResult result = function.InvokeAsync(kernel, new KernelArguments(state), cancellationToken: cancellationToken).GetAwaiter().GetResult();
#pragma warning restore VSTHRD002 // Avoid problematic synchronous waits

        // If return type is complex, serialize the object so it can be deserialized with expected class properties.
        // i.e., class properties can be different if JsonPropertyName = 'id' and class property is 'Id'.
        var returnType = function.Metadata.ReturnParameter.ParameterType;
        var resultAsObject = result.GetValue<object?>();

        if (returnType is not null && !KernelParameterMetadataExtensions.IsPrimitiveOrStringType(returnType))
        {
            var serializedResult = JsonSerializer.Serialize(resultAsObject);
            resultAsObject = JsonSerializer.Deserialize(serializedResult, returnType);
        }

        // TODO (@teresaqhoang): Add model results to execution context + test possible deadlock scenario
        return resultAsObject;
    }
}
