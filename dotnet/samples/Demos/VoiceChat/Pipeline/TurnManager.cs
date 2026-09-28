// Copyright (c) Microsoft. All rights reserved.

public class TurnManager : IDisposable
{
    private int _currentTurnId = 0;
    private CancellationTokenSource _cts = new();
    private readonly object _lock = new();
    public int CurrentTurnId { get { lock (this._lock) { return this._currentTurnId; } } }
    public CancellationToken CurrentToken { get { lock (this._lock) { return this._cts.Token; } } }

    public void Interrupt()
    {
        lock (this._lock)
        {
            this._currentTurnId++;
            this._cts.Cancel();
            this._cts.Dispose();
            this._cts = new CancellationTokenSource();
        }
    }

    public void Dispose() => this._cts?.Dispose();
}
