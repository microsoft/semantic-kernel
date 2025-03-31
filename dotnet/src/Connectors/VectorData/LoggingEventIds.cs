// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Class with event IDs for existing logging messages.
/// </summary>
internal static class LoggingEventIds
{
    public const int CollectionExistsInvoked = 1000;
    public const int CollectionExistsCompleted = 1001;
    public const int CollectionExistsCanceled = 1002;
    public const int CollectionExistsFailed = 1003;

    public const int CreateCollectionInvoked = 1010;
    public const int CreateCollectionCompleted = 1011;
    public const int CreateCollectionCanceled = 1012;
    public const int CreateCollectionFailed = 1013;

    public const int CreateCollectionIfNotExistsInvoked = 1020;
    public const int CreateCollectionIfNotExistsCompleted = 1021;
    public const int CreateCollectionIfNotExistsCanceled = 1022;
    public const int CreateCollectionIfNotExistsFailed = 1023;

    public const int DeleteInvoked = 1030;
    public const int DeleteCompleted = 1031;
    public const int DeleteCanceled = 1032;
    public const int DeleteFailed = 1033;
    public const int DeleteInvokedSensitive = 1034;
    public const int DeleteCompletedSensitive = 1035;

    public const int DeleteBatchInvoked = 1040;
    public const int DeleteBatchCompleted = 1041;
    public const int DeleteBatchCanceled = 1042;
    public const int DeleteBatchFailed = 1043;
    public const int DeleteBatchInvokedSensitive = 1044;
    public const int DeleteBatchCompletedSensitive = 1045;

    public const int DeleteCollectionInvoked = 1050;
    public const int DeleteCollectionCompleted = 1051;
    public const int DeleteCollectionCanceled = 1052;
    public const int DeleteCollectionFailed = 1053;

    public const int GetInvoked = 1060;
    public const int GetCompleted = 1061;
    public const int GetCanceled = 1062;
    public const int GetFailed = 1063;
    public const int GetInvokedSensitive = 1064;
    public const int GetCompletedSensitive = 1065;

    public const int GetBatchInvoked = 1070;
    public const int GetBatchCompleted = 1071;
    public const int GetBatchCanceled = 1072;
    public const int GetBatchFailed = 1073;
    public const int GetBatchInvokedSensitive = 1074;
    public const int GetBatchCompletedSensitive = 1075;

    public const int UpsertInvoked = 1080;
    public const int UpsertCompleted = 1081;
    public const int UpsertCanceled = 1082;
    public const int UpsertFailed = 1083;
    public const int UpsertCompletedSensitive = 1084;

    public const int UpsertBatchInvoked = 1090;
    public const int UpsertBatchCompleted = 1091;
    public const int UpsertBatchCanceled = 1092;
    public const int UpsertBatchFailed = 1093;
    public const int UpsertBatchCompletedSensitive = 1094;

    public const int VectorizedSearchInvoked = 1100;
    public const int VectorizedSearchCompleted = 1101;
    public const int VectorizedSearchCanceled = 1102;
    public const int VectorizedSearchFailed = 1103;

    public const int ListCollectionNamesInvoked = 1110;
    public const int ListCollectionNamesCompleted = 1111;
    public const int ListCollectionNamesCanceled = 1112;
    public const int ListCollectionNamesFailed = 1113;

    public const int HybridSearchInvoked = 1120;
    public const int HybridSearchCompleted = 1121;
    public const int HybridSearchCanceled = 1122;
    public const int HybridSearchFailed = 1123;

    public const int VectorizableTextSearchInvoked = 1130;
    public const int VectorizableTextSearchCompleted = 1131;
    public const int VectorizableTextSearchCanceled = 1132;
    public const int VectorizableTextSearchFailed = 1133;
}
