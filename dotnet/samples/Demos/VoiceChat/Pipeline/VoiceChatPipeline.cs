// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks.Dataflow;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

public class VoiceChatPipeline : IDisposable
{
    // Pipeline configuration constants
    private const int MaxDegreeOfParallelism = 1; // Number of parallel operations in dataflow blocks
    private const int BoundedCapacity = 5; // Maximum capacity for dataflow block buffers
    private const bool EnsureOrdered = true; // Ensure order preservation in pipeline

    // Dataflow options fields - initialized inline
    private readonly ExecutionDataflowBlockOptions _executionOptions = new()
    {
        MaxDegreeOfParallelism = MaxDegreeOfParallelism,
        BoundedCapacity = BoundedCapacity,
        EnsureOrdered = EnsureOrdered
    };

    private readonly DataflowLinkOptions _linkOptions = new() { PropagateCompletion = true };
    private readonly ILogger<VoiceChatPipeline> _logger;
    private readonly AudioPlaybackService _audioPlaybackService;
    private readonly SpeechToTextService _speechToTextService;
    private readonly TextToSpeechService _textToSpeechService;
    private readonly ChatService _chatService;
    private readonly TurnManager _turnManager;
    private readonly VadService _vadService;
    private readonly AudioSourceService _audioSourceService;

    private CancellationTokenSource? _cancellationTokenSource;

    public VoiceChatPipeline(
        ILogger<VoiceChatPipeline> logger,
        AudioPlaybackService audioPlaybackService,
        SpeechToTextService speechToTextService,
        TextToSpeechService textToSpeechService,
        ChatService chatService,
        VadService vadService,
        AudioSourceService audioSourceService,
        TurnManager turnManager,
        IOptions<AudioOptions> audioOptions)
    {
        this._logger = logger;
        this._audioPlaybackService = audioPlaybackService;
        this._speechToTextService = speechToTextService;
        this._textToSpeechService = textToSpeechService;
        this._chatService = chatService;
        this._vadService = vadService;
        this._audioSourceService = audioSourceService;
        this._turnManager = turnManager;
    }

    public async Task RunAsync(CancellationToken cancellationToken = default)
    {
        this._cancellationTokenSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);

        // Create pipeline blocks - VAD now accepts raw audio chunks directly
        var vadBlock = new TransformManyBlock<byte[], AudioEvent>(this._vadService.Transform, this._executionOptions);
        var sttBlock = new TransformBlock<AudioEvent, TranscriptionEvent>(this._speechToTextService.TransformAsync, this._executionOptions);
        var chatBlock = new TransformManyBlock<TranscriptionEvent, ChatEvent>(this._chatService.TransformAsync, this._executionOptions);
        var ttsBlock = new TransformBlock<ChatEvent, SpeechEvent>(this._textToSpeechService.TransformAsync, this._executionOptions);
        var playbackBlock = new ActionBlock<SpeechEvent>(this._audioPlaybackService.PipelineActionAsync, this._executionOptions);

        // Connect the blocks in the pipeline
        this.Link(vadBlock, sttBlock, "VAD", audioData => audioData.Data.Length > 0);
        this.Link(sttBlock, chatBlock, "STT", t => !string.IsNullOrEmpty(t));
        this.Link(chatBlock, ttsBlock, "Chat", t => !string.IsNullOrEmpty(t));
        this.Link(ttsBlock, playbackBlock, "TTS", t => t.Length > 0);

        this._logger.LogInformation("Voice Chat started. You can start conversation now, or press Ctrl+C to exit.");

        try
        {
            // Keep feeding audio chunks into the VAD pipeline block till RunAsync is not cancelled
            await foreach (var audioChunk in this._audioSourceService.GetAudioChunksAsync(this._cancellationTokenSource.Token))
            {
                await vadBlock.SendAsync(audioChunk, this._cancellationTokenSource.Token);
            }
        }
        catch (OperationCanceledException)
        {
            this._logger.LogInformation("Voice Chat pipeline stopping due to cancellation...");
        }
        finally
        {
            vadBlock.Complete();
            await playbackBlock.Completion;
        }
    }

    public void Dispose()
    {
        this._vadService?.Dispose();
        this._cancellationTokenSource?.Dispose();
    }

    // Generic filter methods for pipeline events
    private bool Filter<T>(PipelineEvent<T> evt, string blockName, Func<T, bool> predicate, IDataflowBlock block)
    {
        var valid = PipelineEvent<T>.IsValid(evt, this._turnManager.CurrentTurnId, predicate);
        if (!valid)
        {
            this._logger.LogWarning($"{blockName} block: Event filtered out due to cancellation or empty payload.");
        }
        return valid;
    }

    private bool FilterDiscarded<T>(PipelineEvent<T> evt, string blockName)
    {
        this._logger.LogWarning($"{blockName} block: Event filtered out due to cancellation or empty.");
        return true;
    }

    private void Link<T>(
        ISourceBlock<PipelineEvent<T>> source,
        ITargetBlock<PipelineEvent<T>> target,
        string blockName,
        Func<T, bool> predicate)
    {
        source.LinkTo(target, this._linkOptions, evt => this.Filter(evt, blockName, predicate, source));
        this.DiscardFiltered(source, blockName);
    }

    private void DiscardFiltered<T>(ISourceBlock<PipelineEvent<T>> block, string blockName) => block.LinkTo(DataflowBlock.NullTarget<PipelineEvent<T>>(), this._linkOptions, evt => this.FilterDiscarded(evt, blockName));
}
