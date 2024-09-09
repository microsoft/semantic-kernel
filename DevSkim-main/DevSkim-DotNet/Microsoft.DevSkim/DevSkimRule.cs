using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.ApplicationInspector.RulesEngine;
using Newtonsoft.Json;

namespace Microsoft.DevSkim
{
    public class DevSkimRule : Rule
    {
        [JsonProperty(PropertyName = "fix_its")]
        [JsonPropertyName("fix_its")]
        public List<CodeFix>? Fixes { get; set; }

        [JsonProperty(PropertyName = "recommendation")]
        [JsonPropertyName("recommendation")]
        public string? Recommendation { get; set; }

        [JsonProperty(PropertyName = "confidence")]
        [JsonPropertyName("confidence")]
        public Confidence Confidence { get; set; }

        [JsonProperty(PropertyName = "rule_info")]
        [JsonPropertyName("rule_info")]
        public string? RuleInfo { get; set; }

        public override string ToString()
        {
            return $"'{Id}: {Name}'";
        }
    }
}