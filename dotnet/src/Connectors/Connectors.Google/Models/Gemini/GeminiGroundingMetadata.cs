// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Grounding metadata element.
/// </summary>
public sealed class GeminiGroundingMetadata
{
    /// <summary>
    /// Search entry point information.
    /// </summary>
    [JsonPropertyName("searchEntryPoint")]
    public SearchEntryPointElement SearchEntryPoint { get; set; } = null!;

    /// <summary>
    /// Grounding chunks.
    /// </summary>
    [JsonPropertyName("groundingChunks")]
    public IList<GroundingChunkElement> GroundingChunks { get; set; } = null!;

    /// <summary>
    /// Grounding supports.
    /// </summary>
    [JsonPropertyName("groundingSupports")]
    public IList<GroundingSupportElement> GroundingSupports { get; set; } = null!;

    /// <summary>
    /// Retrieval metadata.
    /// </summary>
    [JsonPropertyName("retrievalMetadata")]
    public Dictionary<string, object> RetrievalMetadata { get; set; } = null!;

    /// <summary>
    /// Web search queries.
    /// </summary>
    [JsonPropertyName("webSearchQueries")]
    public IList<string> WebSearchQueries { get; set; } = null!;

    /// <summary>
    /// Search entry point element.
    /// </summary>
    public sealed class SearchEntryPointElement
    {
        /// <summary>
        /// Rendered content.
        /// </summary>
        [JsonPropertyName("renderedContent")]
        public string RenderedContent { get; set; } = null!;
    }

    /// <summary>
    /// Grounding chunk element.
    /// </summary>
    public sealed class GroundingChunkElement
    {
        /// <summary>
        /// Web information.
        /// </summary>
        [JsonPropertyName("web")]
        public WebElement Web { get; set; } = null!;
    }

    /// <summary>
    /// Web element.
    /// </summary>
    public sealed class WebElement
    {
        /// <summary>
        /// URI of the web resource.
        /// </summary>
        [JsonPropertyName("uri")]
        public string Uri { get; set; } = null!;

        /// <summary>
        /// Title of the web resource.
        /// </summary>
        [JsonPropertyName("title")]
        public string Title { get; set; } = null!;
    }

    /// <summary>
    /// Grounding support element.
    /// </summary>
    public sealed class GroundingSupportElement
    {
        /// <summary>
        /// Segment information.
        /// </summary>
        [JsonPropertyName("segment")]
        public SegmentElement Segment { get; set; } = null!;

        /// <summary>
        /// Grounding chunk indices.
        /// </summary>
        [JsonPropertyName("groundingChunkIndices")]
        public IList<int> GroundingChunkIndices { get; set; } = null!;

        /// <summary>
        /// Confidence scores.
        /// </summary>
        [JsonPropertyName("confidenceScores")]
        public IList<double> ConfidenceScores { get; set; } = null!;
    }

    /// <summary>
    /// Segment element.
    /// </summary>
    public sealed class SegmentElement
    {
        /// <summary>
        /// Start index of the segment.
        /// </summary>
        [JsonPropertyName("startIndex")]
        public int StartIndex { get; set; }

        /// <summary>
        /// End index of the segment.
        /// </summary>
        [JsonPropertyName("endIndex")]
        public int EndIndex { get; set; }

        /// <summary>
        /// Text of the segment.
        /// </summary>
        [JsonPropertyName("text")]
        public string Text { get; set; } = null!;
    }
}
