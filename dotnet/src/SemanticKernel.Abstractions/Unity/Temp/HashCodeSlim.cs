// Copyright (c) Microsoft. All rights reserved.

#if UNITY

namespace System;

/// <summary>
/// Provides utility methods for combining hash codes of multiple values.
/// </summary>
/// <remarks>This class is designed to assist in generating composite hash codes for multiple values. It uses a
/// standard hash code combination algorithm to ensure a good distribution of hash values.</remarks>
/// <remarks>This implementation does not use Microsoft.Bcl.HashCode because that library conflicts with Unity pipeline and splines.</remarks>
internal static class HashCodeSlim
{
    public static int Combine<T1, T2, T3>(T1 value1, T2 value2, T3 value3)
    {
        unchecked
        {
            int hash = 17;
            hash = hash * 31 + (value1?.GetHashCode() ?? 0);
            hash = hash * 31 + (value2?.GetHashCode() ?? 0);
            hash = hash * 31 + (value3?.GetHashCode() ?? 0);
            return hash;
        }
    }

    public static int Combine<T1, T2, T3, T4, T5>(T1 value1, T2 value2, T3 value3, T4 value4, T5 value5)
    {
        unchecked
        {
            int hash = 17;
            hash = hash * 31 + (value1?.GetHashCode() ?? 0);
            hash = hash * 31 + (value2?.GetHashCode() ?? 0);
            hash = hash * 31 + (value3?.GetHashCode() ?? 0);
            hash = hash * 31 + (value4?.GetHashCode() ?? 0);
            hash = hash * 31 + (value5?.GetHashCode() ?? 0);
            return hash;
        }
    }
}
#endif
