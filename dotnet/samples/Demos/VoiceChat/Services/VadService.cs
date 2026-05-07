// Copyright (c) Microsoft. All rights reserved.

using WebRtcVadSharp;

public class VadService : IDisposable
{
    // Voice Activity Detection Constants
    private const int MaxPrerollFrames = 10;             // Maximum number of frames to keep before speech detection
    private const int SilenceThresholdFrames = 20;       // Number of consecutive silent frames to end speech segment
    private const double MinSpeechDurationSeconds = 0.8; // Minimum duration in seconds for valid speech utterance

    private readonly WebRtcVad _vad = new() { OperatingMode = OperatingMode.VeryAggressive };
    private readonly TurnManager _turnManager;

    // State for pipeline processing
    private readonly Queue<byte[]> _preroll = new();
    private readonly List<byte> _speech = [];
    private int _silenceFrames = 0;
    private bool _inSpeech = false;

    public VadService(TurnManager turnManager)
    {
        this._turnManager = turnManager;
    }

    /// <summary>
    /// Pipeline integration method for processing audio chunk events into speech segments.
    /// This method handles the pipeline event creation and processing.
    /// </summary>
    /// <param name="audioChunkEvent">Audio chunk event from the pipeline.</param>
    /// <returns>Audio events when speech segments are detected.</returns>
    public IEnumerable<AudioEvent> Transform(AudioChunkEvent audioChunkEvent)
    {
        foreach (var audioEvent in this.ProcessAudioChunk(audioChunkEvent.Payload))
        {
            yield return audioEvent;
        }
    }

    /// <summary>
    /// Creates an AudioChunkEvent from raw audio data for pipeline processing.
    /// </summary>
    /// <param name="audioChunk">Raw audio chunk from microphone.</param>
    /// <returns>AudioChunkEvent ready for pipeline processing.</returns>
    public AudioChunkEvent CreateAudioChunkEvent(byte[] audioChunk)
    {
        return new AudioChunkEvent(this._turnManager.CurrentTurnId, this._turnManager.CurrentToken, audioChunk);
    }

    /// <summary>
    /// Legacy pipeline integration method for processing raw audio chunks into speech segments.
    /// </summary>
    /// <param name="audioChunk">Raw audio chunk from microphone.</param>
    /// <returns>Audio events when speech segments are detected.</returns>
    public IEnumerable<AudioEvent> Transform(byte[] audioChunk)
    {
        foreach (var audioEvent in this.ProcessAudioChunk(audioChunk))
        {
            yield return audioEvent;
        }
    }

    /// <summary>
    /// Core audio processing logic for speech detection and segmentation.
    /// </summary>
    /// <param name="audioChunk">Raw audio chunk to process.</param>
    /// <returns>Audio events when speech segments are detected.</returns>
    private IEnumerable<AudioEvent> ProcessAudioChunk(byte[] audioChunk)
    {
        bool voiced = this.HasSpeech(audioChunk); // audioChunk expected to be in 20ms chunks

        if (!this._inSpeech)
        {
            this._preroll.Enqueue(audioChunk);
            while (this._preroll.Count > MaxPrerollFrames)
            {
                this._preroll.Dequeue();
            }

            if (voiced)
            {
                this._inSpeech = true;
                while (this._preroll.Count > 0)
                {
                    this._speech.AddRange(this._preroll.Dequeue());
                    this._silenceFrames = 0;
                }
            }
        }
        else
        {
            this._speech.AddRange(audioChunk);
            this._silenceFrames = voiced ? 0 : this._silenceFrames + 1;

            if (this._silenceFrames >= SilenceThresholdFrames)
            {
                var audio = new AudioData(this._speech.ToArray(), AudioOptions.SampleRate, AudioOptions.Channels, AudioOptions.BitsPerSample);
                if (audio.Duration.TotalSeconds > MinSpeechDurationSeconds)
                {
                    this._turnManager.Interrupt();
                    yield return new AudioEvent(this._turnManager.CurrentTurnId, this._turnManager.CurrentToken, audio);
                }
                this._speech.Clear();
                this._inSpeech = false;
                this._silenceFrames = 0;
            }
        }
    }

    public bool HasSpeech(byte[] frame20ms) => this._vad.HasSpeech(frame20ms, SampleRate.Is16kHz, FrameLength.Is20ms);

    public void Dispose() => this._vad.Dispose();
}
