// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData.ProviderServices;

internal interface IRecordCreator
{
    TRecord Create<TRecord>();
}
