// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using System.Text.Json.Serialization;
using Microsoft.ApplicationInspector.RulesEngine;
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;

namespace Microsoft.DevSkim
{
    /// <summary>
    ///     Code fix class
    /// </summary>
    public class CodeFix
    {
        [JsonProperty(PropertyName = "type")]
        [JsonPropertyName("type")]
        [Newtonsoft.Json.JsonConverter(typeof(StringEnumConverter))]
        [System.Text.Json.Serialization.JsonConverter(typeof(JsonStringEnumConverter))]
        public FixType FixType { get; set; } = FixType.RegexReplace;

        [JsonProperty(PropertyName = "name")]
        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonProperty(PropertyName = "pattern")]
        [JsonPropertyName("pattern")]
        public SearchPattern? Pattern { get; set; }

        [JsonProperty(PropertyName = "replacement")]
        [JsonPropertyName("replacement")]
        public string? Replacement { get; set; }
    }
}