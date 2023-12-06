// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using HandlebarsDotNet;
using HandlebarsDotNet.Compiler;
using HandlebarsDotNet.Helpers;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.PromptTemplate.Handlebars.Helpers;
#pragma warning restore IDE0130

/// <summary>
/// Extension class to register additional helpers as Kernel System helpers.
/// </summary>
public static class KernelSystemHelpers
{
    /// <summary>
    /// Register all (default) or specific categories.
    /// </summary>
    /// <param name="handlebarsInstance">The <see cref="IHandlebars"/>-instance.</param>
    /// <param name="variables">Dictionary of variables maintained by the Handlebars context.</param>
    /// <param name="options">Handlebars promnpt template options.</param>
    public static void Register(IHandlebars handlebarsInstance, KernelArguments variables, HandlebarsPromptTemplateOptions options)
    {
        RegisterHandlebarsDotNetHelpers(handlebarsInstance, options);
        RegisterSystemHelpers(handlebarsInstance, variables);
    }

    private static void RegisterHandlebarsDotNetHelpers(IHandlebars handlebarsInstance, HandlebarsPromptTemplateOptions helperOptions)
    {
        HandlebarsHelpers.Register(handlebarsInstance, optionsCallback: options =>
        {
            options.PrefixSeparator = helperOptions.PrefixSeparator;
            options.Categories = helperOptions.Categories;
            options.UseCategoryPrefix = helperOptions.UseCategoryPrefix;
            options.CustomHelperPaths = helperOptions.CustomHelperPaths;
        });
    }

    /// <summary>
    /// Register all system helpers.
    /// </summary>
    /// <param name="handlebarsInstance">The <see cref="IHandlebars"/>-instance.</param>
    /// <param name="variables">Dictionary of variables maintained by the Handlebars context.</param>
    /// <exception cref="KernelException">Exception thrown when a message does not contain a defining role.</exception>
    private static void RegisterSystemHelpers(
        IHandlebars handlebarsInstance,
        KernelArguments variables)
    {
        // TODO [@teresaqhoang]: Issue 3947 Isolate Handlebars Kernel System helpers in their own class
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

        handlebarsInstance.RegisterHelper("json", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            object objectToSerialize = arguments[0];
            string json = objectToSerialize.GetType() == typeof(string) ? (string)objectToSerialize : JsonSerializer.Serialize(objectToSerialize);

            return json;
        });

        handlebarsInstance.RegisterHelper("concat", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            return string.Concat(arguments.Select(var => var?.ToString()));
        });

        handlebarsInstance.RegisterHelper("raw", (writer, options, context, arguments) =>
        {
            options.Template(writer, null);
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

        handlebarsInstance.RegisterHelper("equals", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            object? left = arguments[0];
            object? right = arguments[1];

            return left == right || (left is not null && left.Equals(right));
        });
    }
}
