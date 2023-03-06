// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;
using Qdrant.DotNet.Internal.Diagnostics;

namespace Qdrant.DotNet.Internal.Http.Specs;

internal class FetchVectorsRequest : IValidatable
{
    [JsonPropertyName("limit")]
    private int Limit { get; set; }

    [JsonPropertyName("offset")]
    private int Offset { get; set; }

    [JsonPropertyName("with_payload")]
    private bool WithPayload { get; set; }

    [JsonPropertyName("with_vector")]
    private bool WithVector { get; set; }

    [JsonPropertyName("filter")]
    private Filter Filters { get; set; }

    public static FetchVectorsRequest Fetch(string collectionName)
    {
        return new FetchVectorsRequest(collectionName);
    }
    public void Validate()
    {
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
        this.Filters.Validate();
    }

    public HttpRequestMessage Build()
    {
        this.Validate();
        return HttpRequest.CreatePostRequest(
            $"collections/{this._collectionName}/points/scroll");
    }



    #region private ================================================================================

    private readonly string _collectionName;

    private FetchVectorsRequest(string collectionName)
    {
        this._collectionName = collectionName;
        this.Filters = new Filter();
        this.WithPayload = true;
        this.WithVector = true;

    }

    private class Filter : IValidatable
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
    #endregion

}