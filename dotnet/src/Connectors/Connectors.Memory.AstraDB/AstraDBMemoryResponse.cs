using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

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
}
