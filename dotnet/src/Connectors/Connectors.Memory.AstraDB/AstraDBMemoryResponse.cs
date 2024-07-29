using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.AstraDB
{
  /// <summary>
  /// An AstraDB memory entry.
  /// </summary>
  public class AstraDBMemoryResponse
  {
    [JsonPropertyName("data")]
    public DataContainer Data { get; set; }

    public class DataContainer
    {
      [JsonPropertyName("document")]
      public DocumentContainer Document { get; set; }

      public class DocumentContainer
      {
        [JsonPropertyName("_id")]
        public string InternalId { get; set; }

        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("metadata")]
        public string MetadataString { get; set; }

        [JsonPropertyName("$vector")]
        public List<float> Vector { get; set; }
      }
    }
  }

  /// <summary>
  /// An AstraDB memory entry for AstraDBNearestMatchesResponse.
  /// </summary>
  public class AstraDBNearestMatchesResponse
  {
    [JsonPropertyName("data")]
    public DataContainer Data { get; set; }

    public class DataContainer
    {
      [JsonPropertyName("documents")]
      public List<DocumentContainer> Documents { get; set; }

      public class DocumentContainer
      {
        [JsonPropertyName("_id")]
        public string InternalId { get; set; }

        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("metadata")]
        public string Metadata { get; set; }

        [JsonPropertyName("$vector")]
        public List<float> Vector { get; set; }

        [JsonPropertyName("$similarity")]
        public double Similarity { get; set; }
      }
    }
  }

  public class AstraDBMemoryEntry
  {
    public string Id { get; set; }
    public string MetadataString { get; set; }
    public float[] Vector { get; set; }
    public double Similarity { get; set; }

    public MemoryRecord ToMemoryRecord()
    {
      return MemoryRecord.FromJsonMetadata(
          json: MetadataString,
          embedding: Vector,
          key: Id,
          timestamp: null); // Adjust if timestamp is available
    }
  }
}