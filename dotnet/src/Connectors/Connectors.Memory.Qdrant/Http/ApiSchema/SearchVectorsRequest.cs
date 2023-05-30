// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using static Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema.QdrantFilter;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

internal sealed class SearchVectorsRequest : IValidatable
{
    [JsonPropertyName("vector")]
    public IEnumerable<float> StartingVector { get; set; } = System.Array.Empty<float>();

    [JsonPropertyName("filter")]
    public QdrantFilter Filters { get; set; }

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

    public SearchVectorsRequest SimilarTo(IEnumerable<float> vector)
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
        if (tags == null) { return this; }

        foreach (var tag in tags)
        {
            if (!string.IsNullOrEmpty(tag))
            {
                this.Filters.ValueMustMatch("external_tags", tag);
            }
        }

        return this;
    }

    public SearchVectorsRequest WithFilters(IEnumerable<MemoryFilter>? filters)
    {
        if (filters == null) { return this; }

        foreach (var filter in filters)
        {
            if (!string.IsNullOrEmpty(filter.Field))
            {
                switch (filter.Operator)
                {
                    case MemoryFieldOperator.Equals:
                        this.Filters.Must(new MatchCondition
                        {
                            Key = filter.Field,
                            Match = new Match { Value = filter.Value }
                        });
                        break;
                    case MemoryFieldOperator.GreaterThan:
                        this.Filters.Must(new RangeCondition
                        {
                            Key = filter.Field,
                            Range = new Range { GreaterThan = (float)filter.Value }
                        });
                        break;
                    case MemoryFieldOperator.LowerThan:
                        this.Filters.Must(new RangeCondition
                        {
                            Key = filter.Field,
                            Range = new Range { LowerThan = (float)filter.Value }
                        });
                        break;
                    case MemoryFieldOperator.GreaterThanOrEqual:
                        this.Filters.Must(new RangeCondition
                        {
                            Key = filter.Field,
                            Range = new Range { GreaterThanOrEqual = (float)filter.Value }
                        });
                        break;
                    case MemoryFieldOperator.LowerThanOrEqual:
                        this.Filters.Must(new RangeCondition
                        {
                            Key = filter.Field,
                            Range = new Range { LowerThanOrEqual = (float)filter.Value }
                        });
                        break;
                    case MemoryFieldOperator.Contains:
                        this.Filters.Must(new MatchCondition
                        {
                            Key = filter.Field,
                            Match = new Match { Text = filter.Value }
                        });
                        break;
                    default:
                        break;
                }
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
        this.Filters = new QdrantFilter();
        this.WithPayload = false;
        this.WithVector = false;

        // By default take the closest vector only
        this.FromPosition(0).Take(1);
    }

    #endregion
}
