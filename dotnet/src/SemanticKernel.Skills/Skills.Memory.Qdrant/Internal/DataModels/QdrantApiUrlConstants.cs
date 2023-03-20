
namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;
internal static class QdrantApiUrlConstants
{
    internal static string CreateCollectionUrl(string collectionName) => $"collections/{collectionName}?wait=true";
    internal static string GetCollectionUrl(string collectionName) => $"collections/{collectionName}";
    internal static string DeleteCollectionUrl(string collectionName) => $"collections/{collectionName}?wait=true";
    internal static string GetCollectionsNamesUrl() => $"collections";
    internal static string UpsertPointsUrl(string collectionName) => $"collections/{collectionName}/points?wait=true";
    internal static string DeletePointsUrl(string collectionName) => $"collections/{collectionName}/points?wait=true";
    internal static string SearchPointsUrl(string collectionName) => $"collections/{collectionName}/points/search";
    internal static string BatchPointSearchScoreUrl(string collectionName) => $"collections/{collectionName}/points/search/batch";




}
