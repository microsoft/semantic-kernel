// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Http.Specs;

internal class SearchVectorsRequest : IValidatable
{
    [JsonPropertyName("vector")]
    private float[] StartingVector { get; set; } = System.Array.Empty<float>();

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

    public static SearchVectorsRequest Create(string collectionName)
    {
        return new SearchVectorsRequest(collectionName);
    }

    public static SearchVectorsRequest Create(string collectionName, int vectorSize)
    {
        return new SearchVectorsRequest(collectionName).SimilarTo(new float[vectorSize]);
    }

    public SearchVectorsRequest SimilarTo(float[] vector)
    {
        this.StartingVector = vector;
        return this;
    }

    public SearchVectorsRequest HavingExternalId(string id)
    {
        Verify.NotNullOrEmpty(id, "External ID is empty");
        this.Filters.ValueMustMatch(PointPayloadDataMapper.VECTOR_ID_FIELD, id);
        return this;
    }

    public SearchVectorsRequest HavingTags(IEnumerable<string>? tags)
    {
        if (tags == null) { return this; }

        foreach (var tag in tags)
        {
            if (!string.IsNullOrEmpty(tag))
            {
                this.Filters.ValueMustMatch(PointPayloadDataMapper.VECTOR_TAGS_FIELD, tag);
            }
        }

        return this;
    }

    public SearchVectorsRequest IncludePayLoad()
    {
        this.WithPayload = true;
        return this;
    }

    public SearchVectorsRequest IncludeVectorData()
    {
        this.WithVector = true;
        return this;
    }

    public SearchVectorsRequest FromPosition(int offset)
    {
        this.Offset = offset;
        return this;
    }

    public SearchVectorsRequest Take(int count)
    {
        this.Limit = count;
        return this;
    }

    public SearchVectorsRequest TakeFirst()
    {
        return this.FromPosition(0).Take(1);
    }

    public void Validate()
    {
        Verify.NotNull(this.StartingVector, "Missing target, either provide a vector or a vector size");
        Verify.NotNullOrEmpty(this._collectionName, "The collection name is empty");
        Verify.True(this.Limit > 0, "The number of vectors must be greater than zero");
        this.Filters.Validate();
    }

    public HttpRequestMessage Build()
    {
        this.Validate();
        return HttpRequest.CreatePostRequest(
            $"collections/{this._collectionName}/points/search",
            payload: this);
    }

    #region private ================================================================================

    private readonly string _collectionName;

    private SearchVectorsRequest(string collectionName)
    {
        this._collectionName = collectionName;
        this.Filters = new Filter();
        this.WithPayload = false;
        this.WithVector = false;

        // By default take the closest vector only
        this.FromPosition(0).Take(1);
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
