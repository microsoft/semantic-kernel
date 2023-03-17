using System;
using System.Collections.Generic;

internal class PointSearchData<TEmbedding>
    where TEmbedding : unmanaged
    {
        internal string QdrantId { get; set; } = string.Empty;
        internal TEmbedding[] Vector { get; set; } = Array.Empty<TEmbedding>();
        internal int Version { get; set; }
        internal double? Score { get; set; }
        internal string ExternalId { get; set; } = string.Empty;
        internal Dictionary<string, object> ExternalPayload { get; set; } = new();
        internal List<string> ExternalTags { get; set; } = new();

        internal PointSearchData()
        {
            this.Version = 0;
            this.ExternalTags = new List<string>();
        }
    }