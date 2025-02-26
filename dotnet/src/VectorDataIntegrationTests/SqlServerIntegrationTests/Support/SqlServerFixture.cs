// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public class SqlServerFixture : VectorStoreFixture
{
    public override TestStore TestStore => SqlServerTestStore.Instance;
}
