// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
    internal class Filter : IValidatable
    {
        internal class Match : IValidatable
        {
            [JsonPropertyName("value")]
            internal object Value { get; set; }

            public Match()
            {
                this.Value = string.Empty;
            }

            public void Validate()
            {
            }
        }

        internal class Must : IValidatable
        {
            [JsonPropertyName("key")]
            internal string Key { get; set; }

            [JsonPropertyName("match")]
            internal Match Match { get; set; }

            public Must()
            {
                this.Key = string.Empty;
                this.Match = new();
            }

            public Must(string key, object value) : this()
            {
                this.Key = key;
                this.Match.Value = value;
            }

            public void Validate()
            {
                Verify.NotNullOrEmpty(this.Key, "The filter key is empty");
                Verify.NotNull(this.Match, "The filter match is NULL");
            }
        }

        [JsonPropertyName("must")]
        internal List<Must> Conditions { get; set; }

        internal Filter()
        {
            this.Conditions = new();
        }

        internal Filter ValueMustMatch(string key, object value)
        {
            this.Conditions.Add(new Must(key, value));
            return this;
        }

        public void Validate()
        {
            Verify.NotNull(this.Conditions, "Filter conditions are NULL");
            foreach (var x in this.Conditions)
            {
                x.Validate();
            }
        }
    }
