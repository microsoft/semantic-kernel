namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

internal static class QdrantApiUrlConstants
{
    internal static string CreateCollectionUrl(string collectionName) => $"collections/{collectionName}?wait=true";

    internal static string GetCollectionUrl(string collectionName) => $"collections/{collectionName}";

    internal static string DeleteCollectionUrl(string collectionName) => $"collections/{collectionName}?wait=true";

    internal static string GetCollectionsNamesUrl() => $"collections";

    internal static string RetrievePointUrl(string collectionName, string pointId) => $"collections/{collectionName}/points/{pointId}";

    internal static string GetPointsForCollectionUrl(string collectionName) => $"collections/{collectionName}/points/scroll";

    internal static string UpsertPointsUrl(string collectionName) => $"collections/{collectionName}/points?wait=true";

    internal static string DeletePointUrl(string collectionName) => $"collections/{collectionName}/points/delete?wait=true";

    internal static string SearchPointsUrl(string collectionName) => $"collections/{collectionName}/points/search";

    internal static string BatchPointSearchScoreUrl(string collectionName) => $"collections/{collectionName}/points/search/batch";
}
