using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.AstraDB
{
  /// <summary>
  /// Represents a response from AstraDB containing a single memory entry.
  /// </summary>
  public class AstraDBMemoryResponse
  {
    /// <summary>
    /// Gets or sets the data container holding the document details.
    /// </summary>
    [JsonPropertyName("data")]
    public DataContainer? Data { get; set; }

    /// <summary>
    /// Represents the container for document data in the AstraDB response.
    /// </summary>
    public class DataContainer
    {
      /// <summary>
      /// Gets or sets the document details.
      /// </summary>
      [JsonPropertyName("document")]
      public DocumentContainer? Document { get; set; }

      /// <summary>
      /// Represents the document details within the data container.
      /// </summary>
      public class DocumentContainer
      {
        /// <summary>
        /// Gets or sets the internal identifier for the document.
        /// </summary>
        [JsonPropertyName("_id")]
        public string? InternalId { get; set; }

        /// <summary>
        /// Gets or sets the public identifier for the document.
        /// </summary>
        [JsonPropertyName("id")]
        public string? Id { get; set; }

        /// <summary>
        /// Gets or sets the metadata associated with the document, serialized as a string.
        /// </summary>
        [JsonPropertyName("metadata")]
        public string? MetadataString { get; set; }

        /// <summary>
        /// Gets or sets the vector representing the document embedding.
        /// </summary>
        [JsonPropertyName("$vector")]
        public List<float>? Vector { get; set; } = new List<float>();
      }
    }
  }

  /// <summary>
  /// Represents a response from AstraDB containing multiple nearest matches.
  /// </summary>
  public class AstraDBNearestMatchesResponse
  {
    /// <summary>
    /// Gets or sets the data container holding the list of documents.
    /// </summary>
    [JsonPropertyName("data")]
    public DataContainer? Data { get; set; }

    /// <summary>
    /// Represents the container for multiple document data in the AstraDB nearest matches response.
    /// </summary>
    public class DataContainer
    {
      /// <summary>
      /// Gets or sets the list of document containers, each containing details for a matched document.
      /// </summary>
      [JsonPropertyName("documents")]
      public List<DocumentContainer>? Documents { get; set; } = new List<DocumentContainer>();

      /// <summary>
      /// Represents the document details within the nearest matches data container.
      /// </summary>
      public class DocumentContainer
      {
        /// <summary>
        /// Gets or sets the internal identifier for the document.
        /// </summary>
        [JsonPropertyName("_id")]
        public string? InternalId { get; set; }

        /// <summary>
        /// Gets or sets the public identifier for the document.
        /// </summary>
        [JsonPropertyName("id")]
        public string? Id { get; set; }

        /// <summary>
        /// Gets or sets the metadata associated with the document, serialized as a string.
        /// </summary>
        [JsonPropertyName("metadata")]
        public string? Metadata { get; set; }

        /// <summary>
        /// Gets or sets the vector representing the document embedding.
        /// </summary>
        [JsonPropertyName("$vector")]
        public List<float>? Vector { get; set; } = new List<float>();

        /// <summary>
        /// Gets or sets the similarity score of the document relative to the query.
        /// </summary>
        [JsonPropertyName("$similarity")]
        public double Similarity { get; set; }
      }
    }
  }

  /// <summary>
  /// Represents a memory entry in AstraDB, including details such as ID, metadata, vector, and similarity.
  /// </summary>
  public class AstraDBMemoryEntry
  {
    /// <summary>
    /// Gets or sets the unique identifier for the memory entry.
    /// </summary>
    public string? Id { get; set; }

    /// <summary>
    /// Gets or sets the metadata associated with the memory entry, serialized as a string.
    /// </summary>
    public string? MetadataString { get; set; }

    /// <summary>
    /// Gets or sets the vector representing the embedding for the memory entry.
    /// </summary>
    public float[]? Vector { get; set; }

    /// <summary>
    /// Gets or sets the similarity score of the memory entry.
    /// </summary>
    public double Similarity { get; set; }

    /// <summary>
    /// Converts the AstraDB memory entry to a <see cref="MemoryRecord"/>.
    /// </summary>
    /// <returns>A <see cref="MemoryRecord"/> representing the memory entry.</returns>
    public MemoryRecord ToMemoryRecord()
    {
      return MemoryRecord.FromJsonMetadata(
          json: MetadataString ?? string.Empty,
          embedding: Vector ?? Array.Empty<float>(),
          key: Id ?? string.Empty,
          timestamp: null); // Adjust if timestamp is available
    }
  }
}
