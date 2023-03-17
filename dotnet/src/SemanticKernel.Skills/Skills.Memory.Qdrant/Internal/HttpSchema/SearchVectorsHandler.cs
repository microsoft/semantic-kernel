using System;
using System.Net.Http;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

namespace Micrsoft.SemanticKernel.Skills.Memory.Qdrant.HttpSchema;

internal class SearchVectorsHandler : IValidatable
{
    public enum SearchVectorHandlerType
    {
        Similarity,
        FilterbyScore,
        KeyDataSearch, 
        Delete
    }

    public void Validate()
    {}

    #region private ================================================================================
    private HttpClient? _client;
    #endregion

}