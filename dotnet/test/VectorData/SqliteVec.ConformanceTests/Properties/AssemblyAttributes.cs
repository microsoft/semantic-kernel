// Copyright (c) Microsoft. All rights reserved.

using Xunit;

[assembly: SqliteVec.ConformanceTests.Support.SqliteVecRequired]
// Disable test parallelization in order to prevent from "database is locked" errors
[assembly: CollectionBehavior(DisableTestParallelization = true)]
