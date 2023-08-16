// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Linq.Dynamic.Core;
using System.Linq.Dynamic.Core.CustomTypeProviders;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Web;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;

/// <summary>
/// Different types of interpolation that can be used to transform a prompt string
/// </summary>
public enum PromptInterpolationType
{
    None,
    InterpolateKeys,
    InterpolateFormattable,
    InterpolateDynamicLinqExpression
}

/// <summary>
/// Represents a transformation of an input prompt string that can be template based or customized
/// </summary>
public class PromptTransform
{
    private static readonly Regex s_interpolateRegex = new(@"{(\D.+?)}", RegexOptions.Compiled);

    private static readonly Regex s_interpolateFormattableRegex = new(@"\{(?<token>[^\d\{\},:][^\{\},:]*)(?:,(?<alignment>-?\d+))?(?::(?<format>[^\{\}]+))?\}",
        RegexOptions.Compiled);

    public PromptTransform()
    {
        this.Template = Defaults.EmptyFormat;
        this.TransformFunction = this.DefaultTransform;
    }

    /// <summary>
    /// This is the template used for prompt transformation. It can be a simple string with a {0} token for where to inject the input block or a string with tokens {key} that will be replaced by values from the context, or event complex expressions depending on the interpolation type.
    /// </summary>
    public string Template { get; set; }

    /// <summary>
    /// The type of interpolation to use for the prompt transformation. The default is InterpolateKeys.
    /// </summary>
    public PromptInterpolationType InterpolationType { get; set; } = PromptInterpolationType.InterpolateKeys;

    /// <summary>
    /// The transform function to use for the prompt transformation. The default is a simple interpolation of the template with tokens {key} from a dictionary of values for keys, and then a string format to inject the input in token {0}. This can be customized to use a different interpolation type or a custom function.
    /// </summary>
    [JsonIgnore]
    public Func<string, Dictionary<string, object>?, string> TransformFunction { get; set; }

    /// <summary>
    /// The default transform does interpolation of the template with tokens {key} from a dictionary of values for keys, and then a string format to inject the input in token {0}
    /// </summary>
    public string DefaultTransform(string input, Dictionary<string, object>? context)
    {
        var processedTemplate = this.Template;

        if (context is { Count: > 0 })
        {
            switch (this.InterpolationType)
            {
                case PromptInterpolationType.None:
                    break;
                case PromptInterpolationType.InterpolateKeys:
                    processedTemplate = this.InterpolateKeys(processedTemplate, context);
                    break;
                case PromptInterpolationType.InterpolateFormattable:
                    processedTemplate = this.InterpolateFormattable(processedTemplate, context);
                    break;
                case PromptInterpolationType.InterpolateDynamicLinqExpression:
                    processedTemplate = this.InterpolateDynamicLinqExpression(processedTemplate, context);
                    break;
                default:
                    throw new InvalidOperationException($"Interpolation type {this.InterpolationType} is not supported");
            }
        }

        var toReturn = string.Format(CultureInfo.InvariantCulture, processedTemplate, input);

        return toReturn;
    }

    /// <summary>
    /// Simple interpolation of a string with tokens {key} with a dictionary of values for keys
    /// </summary>
    public string InterpolateKeys(string value, Dictionary<string, object>? context)
    {
        return s_interpolateRegex.Replace(value, match =>
        {
            var key = match.Groups[1].Value;
            if (context?.TryGetValue(key, out var replacementValue) ?? false)
            {
                return string.Format(CultureInfo.InvariantCulture, Defaults.EmptyFormat, replacementValue);
            }

            return string.Empty;
        });
    }

    /// <summary>
    /// More elaborate transformation where actual string interpolation is used through FormattableStringFactory. This is equivalent to $"" executed at runtime with a cost penalty.
    /// </summary>
    public string InterpolateFormattable(string format, Dictionary<string, object> context)
    {
        return s_interpolateFormattableRegex.Replace(format,
            match =>
            {
                var key = match.Groups["token"].Value;
                var alignment = match.Groups["alignment"].Value;
                var formatSpec = match.Groups["format"].Value;

                if (context.TryGetValue(key, out var replacementValue))
                {
                    // Construct the format token
                    var formatToken = "{0";
                    if (!string.IsNullOrEmpty(alignment))
                    {
                        formatToken += "," + alignment;
                    }

                    if (!string.IsNullOrEmpty(formatSpec))
                    {
                        formatToken += ":" + formatSpec;
                    }

                    formatToken += "}";

                    // Directly use FormattableStringFactory to interpolate the value
                    var interpolatedValue = FormattableStringFactory.Create(formatToken, replacementValue);
                    return interpolatedValue.ToString(CultureInfo.InvariantCulture);
                }

                return "";
            });
    }

    private static ConcurrentDictionary<string, Delegate> s_cachedInterpolationLinqExpressions = new();

    /// <summary>
    /// Most advanced interpolation that uses DynamicLinq to parse and compile a lambda expression at runtime.
    /// </summary>
    /// <remarks>
    /// Warning: Please be careful when using this feature as it can be a security risk if the input is not sanitized.
    /// </remarks>
    public string InterpolateDynamicLinqExpression(string value, Dictionary<string, object> context)
    {
        return s_interpolateRegex.Replace(value,
            match =>
            {
                var matchToken = match.Groups[1].Value;
                var key = $"{value}/{matchToken}";
                if (!s_cachedInterpolationLinqExpressions.TryGetValue(key, out var tokenDelegate))
                {
                    var parameters = new List<ParameterExpression>(context.Count);
                    foreach (var contextObject in context)
                    {
                        var p = Expression.Parameter(contextObject.Value.GetType(), contextObject.Key);
                        parameters.Add(p);
                    }

                    ParsingConfig config = new();
                    config.CustomTypeProvider = new CustomDynamicTypeProvider(context, config.CustomTypeProvider);

                    var e = System.Linq.Dynamic.Core.DynamicExpressionParser.ParseLambda(config, parameters.ToArray(), null, matchToken);
                    tokenDelegate = e.Compile();
                    s_cachedInterpolationLinqExpressions[key] = tokenDelegate;
                }

                return (tokenDelegate.DynamicInvoke(context.Values.ToArray()) ?? "").ToString();
            });
    }

    private sealed class CustomDynamicTypeProvider : IDynamicLinkCustomTypeProvider
    {
        private readonly Dictionary<string, object> _context;

        public CustomDynamicTypeProvider(Dictionary<string, object> context, IDynamicLinkCustomTypeProvider dynamicLinkCustomTypeProvider)
        {
            this._context = context;
            this.DefaultProvider = dynamicLinkCustomTypeProvider;
        }

        public IDynamicLinkCustomTypeProvider DefaultProvider { get; set; }

        public HashSet<Type> GetCustomTypes()
        {
            HashSet<Type> types = this.DefaultProvider.GetCustomTypes();
            types.Add(typeof(string));
            types.Add(typeof(Regex));
            types.Add(typeof(RegexOptions));
            types.Add(typeof(CultureInfo));
            types.Add(typeof(HttpUtility));
            types.Add(typeof(Enumerable));
            foreach (var contextObject in this._context)
            {
                types.Add(contextObject.Value.GetType());
            }

            return types;
        }

        public Dictionary<Type, List<MethodInfo>> GetExtensionMethods()
        {
            return this.DefaultProvider.GetExtensionMethods();
        }

        public Type? ResolveType(string typeName)
        {
            return this.DefaultProvider.ResolveType(typeName);
        }

        public Type? ResolveTypeBySimpleName(string simpleTypeName)
        {
            return this.DefaultProvider.ResolveTypeBySimpleName(simpleTypeName);
        }
    }
}
