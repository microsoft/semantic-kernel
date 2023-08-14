using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings
{
    /// <summary>
    /// Represents a transformation of an input prompt string that can be template based or customized
    /// </summary>
    public class PromptTransform
    {
        private static readonly Regex s_interpolateRegex = new(@"{(\D.+?)}", RegexOptions.Compiled);

        public PromptTransform()
        {
            this.Template = Defaults.PromptTransformTemplate;
            this.TransformFunction = this.DefaultTransform;
        }

        public string Template { get; set; }

        [JsonIgnore]
        public Func<string, Dictionary<string, string>?, string> TransformFunction { get; set; }

        public string DefaultTransform(string input, Dictionary<string, string>? context)
        {
            var processedTemplate = this.Template;

            if (context is { Count: > 0 })
            {
                processedTemplate = this.Interpolate(processedTemplate, context);
            }

            var toReturn = string.Format(CultureInfo.InvariantCulture, processedTemplate, input);

            return toReturn;
        }

        public string Interpolate(string value, Dictionary<string, string>? context)
        {
            return s_interpolateRegex.Replace(value, match =>
            {
                var key = match.Groups[1].Value;
                if (context.TryGetValue(key, out var replacementValue))
                {
                    return replacementValue;
                }

                return string.Empty;
            });
        }
    }
}
