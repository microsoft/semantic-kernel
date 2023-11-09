// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;
using HandlebarsDotNet;
using System.Text.Json;
using HandlebarsDotNet.Compiler;
using System.Collections.Generic;
using System.Threading;
using System;
using System.Linq;
using System.Globalization;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Planners.Handlebars;

/// <summary>
/// Provides extension methods for rendering Handlebars templates in the context of a Semantic Kernel.
/// </summary>
public static class HandlebarsTemplateEngineExtensions
{
    /// <summary>
    /// The key used to store the reserved output type in the dictionary of variables passed to the Handlebars template engine.
    /// </summary>
    public static readonly string ReservedOutputTypeKey = "RESERVED_OUTPUT_TYPE";

    /// <summary>
    /// Renders a Handlebars template in the context of a Semantic Kernel.
    /// </summary>
    /// <param name="kernel">The Semantic Kernel.</param>
    /// <param name="executionContext">The execution context.</param>
    /// <param name="template">The Handlebars template to render.</param>
    /// <param name="variables">The dictionary of variables to pass to the Handlebars template engine.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The rendered Handlebars template.</returns>
    public static string Render
    (
        IKernel kernel,
        SKContext executionContext,
        string template,
        Dictionary<string, object?> variables,
        CancellationToken cancellationToken = default
    )
    {
        IHandlebars handlebarsInstance = HandlebarsDotNet.Handlebars.Create(
            new HandlebarsConfiguration
            {
                NoEscape = true
            });

        // Add helpers for each function
        foreach (FunctionView function in kernel.Functions.GetFunctionViews())
        {
            RegisterFunctionAsHelper(kernel, executionContext, handlebarsInstance, function, variables, cancellationToken);
        }

        // Add system helpers
        RegisterSystemHelpers(handlebarsInstance, variables);

        var compiledTemplate = handlebarsInstance.Compile(template);
        return compiledTemplate(variables);
    }

    private static void RegisterFunctionAsHelper(
        IKernel kernel,
        SKContext executionContext,
        IHandlebars handlebarsInstance,
        FunctionView functionView,
        Dictionary<string, object?> variables,
        CancellationToken cancellationToken = default)
    {
        string fullyResolvedFunctionName = functionView.PluginName + "-" + functionView.Name;

        handlebarsInstance.RegisterHelper(fullyResolvedFunctionName, (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            // Get the parameters from the template arguments
            if (arguments.Any())
            {
                if (arguments[0].GetType() == typeof(HashParameterDictionary))
                {
                    // Process hash arguments
                    var handlebarArgs = arguments[0] as IDictionary<string, object>;

                    // Prepare the input parameters for the function
                    foreach (var param in functionView.Parameters)
                    {
                        // TODO: accomodate ServerUrl override? 
                        if (param.Name.Contains("server_url") || param.Name.Contains("server-url"))
                        {
                            continue;
                        }

                        var fullyQualifiedParamName = functionView.Name + "-" + param.Name;
                        var value = handlebarArgs != null && (handlebarArgs.TryGetValue(param.Name, out var val) || handlebarArgs.TryGetValue(fullyQualifiedParamName, out val)) ? val : null;

                        if (value != null && (handlebarArgs?.ContainsKey(param.Name) == true || handlebarArgs?.ContainsKey(fullyQualifiedParamName) == true))
                        {
                            if (variables.ContainsKey(param.Name))
                            {
                                variables[param.Name] = value;
                            }
                            else
                            {
                                variables.Add(param.Name, value);
                            }
                        }
                        else // TODO: HACK - Need this is a workaround for missing remote function parameters (issue with how we use reflection to port in function details with complex types)
                            if (param.Name == "input" && (!handlebarArgs?.ContainsKey("input") == true || !handlebarArgs?.ContainsKey(fullyQualifiedParamName) == true))
                        {
                            // Assign first argument value as input value
                            variables[param.Name] = handlebarArgs?.First().Value;
                        }
                        else if (param.IsRequired == true)
                        {
                            throw new SKException($"Parameter {param.Name} is required for function {functionView.Name}.");
                        }
                    }
                }
                else
                {
                    // Process positional arguments
                    var requiredParameters = functionView.Parameters.Where(p => p.IsRequired == true).ToList();
                    if (arguments.Length >= requiredParameters.Count && arguments.Length <= functionView.Parameters.Count)
                    {
                        var argIndex = 0;
                        foreach (var arg in arguments)
                        {
                            var param = functionView.Parameters[argIndex];
                            if (IsExpectedParameterType(param.Type.ToString() ?? "", arg.GetType().Name, arg))
                            {
                                if (variables.ContainsKey(param.Name))
                                {
                                    variables[param.Name] = arguments[argIndex];
                                }
                                else
                                {
                                    variables.Add(param.Name, arguments[argIndex]);
                                }
                                argIndex++;
                            }
                            else
                            {
                                throw new SKException($"Invalid parameter type for function {functionView.Name}. Parameter {param.Name} expects type {param.Type} but received {arguments[argIndex].GetType()}.");
                            }
                        }
                    }
                    else
                    {
                        throw new SKException($"Invalid parameter count for function {functionView.Name}. {arguments.Length} were specified but {functionView.Parameters.Count} are required.");
                    }
                }
            }

            foreach (var v in variables)
            {
                var varString = v.Value?.ToString() ?? "";
                if (executionContext.Variables.TryGetValue(v.Key, out var argVal))
                {
                    executionContext.Variables[v.Key] = varString;
                }
                else
                {
                    executionContext.Variables.Add(v.Key, varString);
                }
            }

            ISKFunction function = kernel.Functions.GetFunction(functionView.PluginName, functionView.Name);
            // TODO (@teresaqhoang): Add model results to execution context + test possible deadlock scenario
            KernelResult result = kernel.RunAsync(executionContext.Variables, cancellationToken, function).GetAwaiter().GetResult();

            // Write the result to the template
            return result.GetValue<object?>();
        });
    }

    private static void RegisterSystemHelpers(
        IHandlebars handlebarsInstance,
        Dictionary<string, object?> variables
    )
    {
        handlebarsInstance.RegisterHelper("array", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            // Convert all the arguments to an array
            var array = arguments.Select(a => a).ToList();

            return array;
        });

        handlebarsInstance.RegisterHelper("range", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            var start = int.Parse(arguments[0].ToString(), CultureInfo.InvariantCulture);
            var end = int.Parse(arguments[1].ToString(), CultureInfo.InvariantCulture);

            var count = end - start;

            // Create array from start to end
            var array = Enumerable.Range(start, count).Select(i => (object)i).ToList();

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

        handlebarsInstance.RegisterHelper("equal", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            object? left = arguments[0];
            object? right = arguments[1];

            return left == right || (left != null && left.Equals(right));
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
                throw new SKException("Message must have a role.");
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
            if (arguments[0].GetType() == typeof(HashParameterDictionary))
            {
                // Get the parameters from the template arguments
                var parameters = arguments[0] as IDictionary<string, object>;

                if (variables.TryGetValue((string)parameters!["name"], out var value))
                {
                    variables[(string)parameters!["name"]] = value;
                }
                else
                {
                    variables.Add((string)parameters!["name"], value);
                }
            }
            else
            {
                var name = arguments[0].ToString();
                if (variables.TryGetValue(name, out var value))
                {
                    variables[name] = value;
                }
                else
                {
                    variables.Add(name, value);
                }
            }
        });

        handlebarsInstance.RegisterHelper("get", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            var value = new object();
            if (arguments[0].GetType() == typeof(HashParameterDictionary))
            {
                var parameters = arguments[0] as IDictionary<string, object>;
                value = variables[(string)parameters!["name"]];
            }
            else
            {
                value = variables[arguments[0].ToString()];
            }

            return value;
        });
    }

    private static bool IsNumericType(string typeStr)
    {
        Type? type = typeStr.IsNullOrEmpty() ? Type.GetType(typeStr) : null;

        if (type == null)
        {
            return false;
        }

        return Type.GetTypeCode(type) switch
        {
            TypeCode.Byte or TypeCode.Decimal or TypeCode.Double or TypeCode.Int16 or TypeCode.Int32 or TypeCode.Int64 or TypeCode.SByte or TypeCode.Single or TypeCode.UInt16 or TypeCode.UInt32 or TypeCode.UInt64 => true,
            _ => false,
        };
    }

    private static bool TryParseAnyNumber(string input)
    {
        // Check if input can be parsed as any of these numeric types  
        return int.TryParse(input, out _)
            || double.TryParse(input, out _)
            || float.TryParse(input, out _)
            || long.TryParse(input, out _)
            || decimal.TryParse(input, out _)
            || short.TryParse(input, out _)
            || byte.TryParse(input, out _)
            || sbyte.TryParse(input, out _)
            || ushort.TryParse(input, out _)
            || uint.TryParse(input, out _)
            || ulong.TryParse(input, out _);
    }

    private static double CastToNumber(object? number)
    {
        if (number is int numberInt)
        {
            return numberInt;
        }
        else if (number is decimal numberDecimal)
        {
            return (double)numberDecimal;
        }
        else
        {
            return double.Parse(number!.ToString()!, CultureInfo.InvariantCulture);
        }
    }

    /*
     * Type check will pass if:
     * Types are an exact match.
     * Handlebar argument is any kind of numeric type if function parameter requires a numeric type.
     * Handlebar argument type is an object (this covers complex types).
     * Function parameter is a generic type.
     */
    private static bool IsExpectedParameterType(string functionViewType, string handlebarArgumentType, object handlebarArgValue)
    {
        var isValidNumericType = IsNumericType(functionViewType) && IsNumericType(handlebarArgumentType);
        if (IsNumericType(functionViewType) && !IsNumericType(handlebarArgumentType))
        {
            isValidNumericType = TryParseAnyNumber(handlebarArgValue.ToString());
        }

        return functionViewType == handlebarArgumentType || isValidNumericType || handlebarArgumentType == "object";
    }
}