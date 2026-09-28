// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.Extensions.Logging;
using NAudio.Wave;

public class AudioSourceService
{
    private const int BitsPerByte = 8;
    private const int MillisecondsPerSecond = 1000;

    private readonly ILogger<AudioSourceService> _logger;
    private readonly int _frameBytes;
    private readonly WaveFormat _waveFormat;

    public AudioSourceService(ILogger<AudioSourceService> logger)
    {
        this._logger = logger;

        // Calculate frame size in bytes: (samples/sec * channels * bits/sample * milliseconds) / (bits/byte * ms/sec)
        this._frameBytes = (AudioOptions.SampleRate * AudioOptions.Channels * AudioOptions.BitsPerSample * AudioOptions.BufferMilliseconds) / (BitsPerByte * MillisecondsPerSecond);

        this._waveFormat = new WaveFormat(AudioOptions.SampleRate, AudioOptions.BitsPerSample, AudioOptions.Channels);
    }

    // Generate audio chunks from the microphone input.
    public async IAsyncEnumerable<byte[]> GetAudioChunksAsync([EnumeratorCancellation] CancellationToken token = default)
    {
        var chunks = new Queue<byte[]>();
        var tcs = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        var semaphore = new SemaphoreSlim(0);

        using var waveIn = new WaveInEvent
        {
            WaveFormat = this._waveFormat,
            BufferMilliseconds = AudioOptions.BufferMilliseconds
        };

        waveIn.RecordingStopped += (_, e) => tcs.TrySetResult();

        waveIn.DataAvailable += (_, e) =>
        {
            if (e.Buffer.Length == this._frameBytes)
            {
                chunks.Enqueue(e.Buffer);
                semaphore.Release();
            }
            else
            {
                this._logger.LogWarning($"Ignoring received audio data of unexpected length: {e.Buffer.Length} bytes. Expected {this._frameBytes}");
            }
        };

        waveIn.StartRecording();
        try
        {
            while (!token.IsCancellationRequested)
            {
                await semaphore.WaitAsync(token).ConfigureAwait(false);
                if (chunks.TryDequeue(out var chunk))
                {
                    yield return chunk;
                }
            }
        }
        finally
        {
            waveIn.StopRecording();
            await tcs.Task.ConfigureAwait(false);
        }
    }
}
