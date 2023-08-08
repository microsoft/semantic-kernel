// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

using System.Threading;

public class CallRequestCostCreditor
{
    private long _ongoingCostInTicks; // We use long to store the value, which will allow atomic operations

    public decimal OngoingCost
    {
        get => this.DecimalFromTicks(Interlocked.Read(ref this._ongoingCostInTicks)); // Read the value atomically
    }

    public void Reset()
    {
        Interlocked.Exchange(ref this._ongoingCostInTicks, 0);
    }

    public void Credit(decimal cost)
    {
        long tickChange = this.TicksFromDecimal(cost);
        Interlocked.Add(ref this._ongoingCostInTicks, tickChange);
    }

    private long TicksFromDecimal(decimal value)
    {
        // Convert the decimal value to an equivalent long value (e.g., by scaling)
        return (long)(value * 1_000_000_000); // Assuming 6 decimal places of precision
    }

    private decimal DecimalFromTicks(long ticks)
    {
        return ticks / 1_000_000m; // Convert back to decimal
    }
}
