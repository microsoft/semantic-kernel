// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using NAudio.Wave;

public class AudioPlaybackService(ILogger<AudioPlaybackService> logger) : IDisposable
{
    private readonly ILogger<AudioPlaybackService> _logger = logger;
    private WaveOutEvent? _waveOut;
    private bool _isPlaying;

    public Task PipelineActionAsync(SpeechEvent evt) => this.PlayAudioAsync(evt.Payload, evt.CancellationToken);

    public void Dispose() => this._waveOut?.Dispose();

    private async Task PlayAudioAsync(byte[] audioData, CancellationToken cancellationToken = default)
    {
        if (this._isPlaying)
        {
            this._logger.LogError("Ignoring audio playback. Already playing.");
            return;
        }

        this._logger.LogInformation("Starting audio playback...");

        try
        {
            using var audioStream = new MemoryStream(audioData);
            using var audioFileReader = new Mp3FileReader(audioStream);

            this._waveOut = new WaveOutEvent();
            var tcs = new TaskCompletionSource();

            this._waveOut.PlaybackStopped += (sender, e) =>
            {
                this._isPlaying = false;
                tcs.TrySetResult();
                if (e.Exception != null)
                {
                    this._logger.LogWarning($"Playback error occurred: {e.Exception.Message}");
                }
            };

            this._waveOut.Init(audioFileReader);
            this._isPlaying = true;
            this._waveOut.Play();

            this._logger.LogInformation("Audio chunk playback started. You can speak to interrupt.");

            // Wait for playback to complete or cancellation
            await using (cancellationToken.Register(() =>
            {
                this._logger.LogInterrupted();
                this?._waveOut.Stop();
                tcs.TrySetCanceled();
            }))
            {
                await tcs.Task.ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException)
        {
            this._logger.LogInterrupted();
            this._isPlaying = false;
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Error during audio playback");
            this._isPlaying = false;
            throw;
        }
        finally
        {
            this._waveOut?.Dispose();
            this._waveOut = null;
        }
    }
}
