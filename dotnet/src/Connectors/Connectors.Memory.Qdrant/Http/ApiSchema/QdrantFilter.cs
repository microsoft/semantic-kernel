// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;
public sealed class QdrantFilter : IValidatable
{
    [JsonPropertyName("must")]
    public List<Condition> Conditions { get; set; } = new();

    public void Validate()
    {
        Verify.NotNullOrEmpty(this.Conditions, "No conditions in the filter");
        foreach (var condition in this.Conditions)
        {
            condition.Validate();
        }
    }

    public QdrantFilter Must(params Condition[] conditions)
    {
        this.Conditions.AddRange(conditions);
        return this;
    }
    internal QdrantFilter ValueMustMatch(string key, object value)
    {
        this.Conditions.Add(new MatchCondition
        {
            Key = key,
            Match = new Match { Value = value }
        });

        return this;
    }

    internal QdrantFilter CoordinatesWithinRadius(string key,
        GeoRadius radius)
    {
        this.Conditions.Add(new GeoRadiusCondition
        {
            Key = key,
            GeoRadius = radius
        });

        return this;
    }

    public abstract class Condition : IValidatable
    {
        [JsonPropertyName("key")]
        public string Key { get; set; } = string.Empty;

        public abstract void Validate();
    }

    public sealed class MatchCondition : Condition, IValidatable
    {
        [JsonPropertyName("match")]
        public Match? Match { get; set; }

        public override void Validate()
        {
            Verify.NotNullOrEmpty(this.Key, "Match key is NULL");
            Verify.NotNull(this.Match, "Match condition is NULL");
            this.Match!.Validate();
        }
    }

    public sealed class RangeCondition : Condition
    {
        [JsonPropertyName("range")]
        public Range? Range { get; set; }

        public override void Validate()
        {
            Verify.NotNullOrEmpty(this.Key, "Match key is NULL");
            Verify.NotNull(this.Range, "Range condition is NULL");
            this.Range!.Validate();
        }
    }

    public sealed class GeoBoundingBoxCondition : Condition, IValidatable
    {
        [JsonPropertyName("geo_bounding_box")]
        public GeoBoundingBox? GeoBoundingBox { get; set; }

        public override void Validate()
        {
            Verify.NotNullOrEmpty(this.Key, "Match key is NULL");
            Verify.NotNull(this.GeoBoundingBox, "Geo bounding box condition is NULL");
            this.GeoBoundingBox!.Validate();
        }
    }

    public sealed class GeoRadiusCondition : Condition, IValidatable
    {
        [JsonPropertyName("geo_radius")]
        public GeoRadius? GeoRadius { get; set; }

        public override void Validate()
        {
            Verify.NotNullOrEmpty(this.Key, "Match key is NULL");
            Verify.NotNull(this.GeoRadius, "Geo radius condition is NULL");
            this.GeoRadius!.Validate();
        }
    }

    public sealed class Range : IValidatable
    {
        public float? GreaterThan { get; set; }
        public float? GreaterThanOrEqual { get; set; }
        public float? LowerThan { get; set; }
        public float? LowerThanOrEqual { get; set; }

        public void Validate()
        {
            Verify.True(this.GreaterThan.HasValue
                || this.GreaterThanOrEqual.HasValue
                || this.LowerThan.HasValue
                || this.LowerThanOrEqual.HasValue,
                "No range conditions are specified");
        }
    }
    public class Match : IValidatable
    {
        public object? Value { get; set; }
        public object? Text { get; set; }
        public List<object>? Any { get; set; }
        public List<object>? Except { get; set; }

        public void Validate()
        {
            Verify.True(
                this.Value != null
                || this.Text != null
                || this.Any != null
                || this.Except != null,
                "No match conditions are specified");
        }
    }

    public class GeoRadius : IValidatable
    {
        public GeoRadius(Coordinates center, float radius)
        {
            this.Center = center;
            this.Radius = radius;
        }

        public Coordinates Center { get; set; }
        public float Radius { get; set; }

        public void Validate()
        {
            Verify.NotNull(this.Center, "Geo radius center is NULL");
        }
    }

    public class GeoBoundingBox : IValidatable
    {
        public GeoBoundingBox(Coordinates bottomRight, Coordinates topLeft)
        {
            this.BottomRight = bottomRight;
            this.TopLeft = topLeft;
        }

        public Coordinates BottomRight { get; set; }
        public Coordinates TopLeft { get; set; }

        public void Validate()
        {
            Verify.NotNull(this.BottomRight, "Geo bounding box bottom right is NULL");
            Verify.NotNull(this.TopLeft, "Geo bounding box top left is NULL");
        }
    }

    public class Coordinates : IValidatable
    {
        public Coordinates(float latitude, float longitude)
        {
            this.Latitude = latitude;
            this.Longitude = longitude;
        }

        public float Latitude { get; set; }
        public float Longitude { get; set; }

        public void Validate()
        {
            Verify.True(this.Latitude >= -90 && this.Latitude <= 90, "Latitude is out of range");
            Verify.True(this.Longitude >= -180 && this.Longitude <= 180, "Longitude is out of range");
        }
    }
}
