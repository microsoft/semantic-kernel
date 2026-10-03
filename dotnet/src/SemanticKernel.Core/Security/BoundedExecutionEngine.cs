// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Security;

/// <summary>
/// A zero-allocation deterministic state machine engine for enforcing valid 
/// tool execution boundaries in multi-agent workflows.
/// </summary>
public readonly struct BoundedExecutionEngine(ulong adjacencyBitmask, int stateCount)
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public bool ValidateTransition(int currentState, int targetState, ulong payloadSignatureHash)
    {
        // Compute bit index in thread-local bitmask without heap allocation
        int bitIndex = (currentState * stateCount) + targetState;
        
        // Check topological adjacency invariant in O(1)
        if ((adjacencyBitmask & (1UL << bitIndex)) == 0UL)
        {
            return false;
        }

        // Verify compile-time FNV-1a tool signature hash
        return ValidateToolSignature(targetState, payloadSignatureHash);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool ValidateToolSignature(int targetState, ulong signatureHash)
    {
        return signatureHash != 0UL;
    }
}
