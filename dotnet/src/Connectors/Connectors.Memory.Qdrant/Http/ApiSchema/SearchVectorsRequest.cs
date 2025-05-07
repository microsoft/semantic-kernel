// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
internal sealed class SearchVectorsRequest
{
    [JsonPropertyName("vector")]
    public ReadOnlyMemory<float> StartingVector { get; set; }

    [JsonPropertyName("filter")]
    public Filter Filters { get; set; }

    [JsonPropertyName("limit")]
    public int Limit { get; set; }

    [JsonPropertyName("offset")]
    public int Offset { get; set; }

    [JsonPropertyName("with_payload")]
    public bool WithPayload { get; set; }

    [JsonPropertyName("with_vector")]
    public bool WithVector { get; set; }

    [JsonPropertyName("score_threshold")]
    public double ScoreThreshold { get; set; } = -1;

    public static SearchVectorsRequest Create(string collectionName)
    {
        return new SearchVectorsRequest(collectionName);
    }

    public static SearchVectorsRequest Create(string collectionName, int vectorSize)
    {
        return new SearchVectorsRequest(collectionName).SimilarTo(new float[vectorSize]);
    }

    public SearchVectorsRequest SimilarTo(ReadOnlyMemory<float> vector)
    {
        this.StartingVector = vector;
        return this;
    }

    public SearchVectorsRequest HavingExternalId(string id)
    {
        Verify.NotNull(id, "External ID is NULL");
        this.Filters.ValueMustMatch("id", id);
        return this;
    }

    public SearchVectorsRequest HavingTags(IEnumerable<string>? tags)
    {
        if (tags is null) { return this; }

        foreach (var tag in tags)
        {
            if (!string.IsNullOrEmpty(tag))
            {
                this.Filters.ValueMustMatch("external_tags", tag);
            }
        }

        return this;
    }

    public SearchVectorsRequest WithScoreThreshold(double threshold)
    {
        this.ScoreThreshold = threshold;
        return this;
    }

    public SearchVectorsRequest IncludePayLoad()
    {
        this.WithPayload = true;
        return this;
    }

    public SearchVectorsRequest IncludeVectorData(bool withVector)
    {
        this.WithVector = withVector;
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

    public HttpRequestMessage Build()
    {
        Verify.NotNull(this.StartingVector);
        Verify.NotNullOrWhiteSpace(this._collectionName);
        Verify.True(this.Limit > 0, "The number of vectors must be greater than zero");
        this.Filters.Validate();

        return HttpRequest.CreatePostRequest(
            $"collections/{this._collectionName}/points/search",
            payload: this);
    }

    internal sealed class Filter
    {
        internal sealed class Match
        {
            [JsonPropertyName("value")]
            public object Value { get; set; }

            public Match()
            {
                this.Value = string.Empty;
            }
        }

        internal sealed class Must
        {
            [JsonPropertyName("key")]
            public string Key { get; set; }

            [JsonPropertyName("match")]
            public Match Match { get; set; }

            public Must()
            {
                this.Match = new();
                this.Key = string.Empty;
            }

            public Must(string key, object value) : this()
            {
                this.Key = key;
                this.Match.Value = value;
            }

            public void Validate()
            {
                Verify.NotNull(this.Key, "The filter key is NULL");
                Verify.NotNull(this.Match, "The filter match is NULL");
            }
        }

        [JsonPropertyName("must")]
        public List<Must> Conditions { get; set; }

        internal Filter()
        {
            this.Conditions = [];
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

    #endregion
}
