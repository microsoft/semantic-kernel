// Copyright (c) Microsoft. All rights reserved.

global using AudioChunkEvent = PipelineEvent<byte[]>;
global using AudioEvent = PipelineEvent<AudioData>;
global using ChatEvent = PipelineEvent<string>;
global using SpeechEvent = PipelineEvent<byte[]>;
global using TranscriptionEvent = PipelineEvent<string?>;

public readonly struct PipelineEvent<T>(int turnId, CancellationToken cancellationToken, T payload) : IEquatable<PipelineEvent<T>>
{
    public int TurnId { get; } = turnId;
    public CancellationToken CancellationToken { get; } = cancellationToken;
    public T Payload { get; } = payload;

    public static bool IsValid(PipelineEvent<T> evt, int currentTurnId, Func<T, bool>? payloadPredicate = null)
        => evt.Payload != null
            && evt.TurnId == currentTurnId
            && !evt.CancellationToken.IsCancellationRequested
            && (payloadPredicate?.Invoke(evt.Payload) ?? true);

    public override bool Equals(object obj)
    {
        throw new NotImplementedException();
    }

    public override int GetHashCode()
    {
        throw new NotImplementedException();
    }

    public static bool operator ==(PipelineEvent<T> left, PipelineEvent<T> right)
    {
        return left.Equals(right);
    }

    public static bool operator !=(PipelineEvent<T> left, PipelineEvent<T> right)
    {
        return !(left == right);
    }

    public bool Equals(PipelineEvent<T> other)
    {
        throw new NotImplementedException();
    }
}

public record AudioData(byte[] Data, int SampleRate, int Channels, int BitsPerSample)
{
    public TimeSpan Duration => TimeSpan.FromSeconds((double)this.Data.Length / (this.SampleRate * this.Channels * this.BitsPerSample / 8));
}
