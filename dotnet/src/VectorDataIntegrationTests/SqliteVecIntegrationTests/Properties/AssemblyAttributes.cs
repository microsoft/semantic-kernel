// Copyright (c) Microsoft. All rights reserved.

using Xunit;

[assembly: SqliteVecIntegrationTests.Support.SqliteVecRequired]
// Disable test parallelization in order to prevent from "database is locked" errors
[assembly: CollectionBehavior(DisableTestParallelization = true)]
