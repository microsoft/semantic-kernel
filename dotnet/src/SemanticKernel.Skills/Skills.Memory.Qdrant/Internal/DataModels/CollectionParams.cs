// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.DataModels;

internal class CollectionConfig
{
    [JsonPropertyName("params")]
    internal CollectionParams? Params { get; set; }

    [JsonPropertyName("hnsw_config")]
    internal CollectionHnswConfig? HnswConfig { get; set; }

    [JsonPropertyName("optimizer_config")]
    internal CollectionOptimizerConfig? OptimizerConfig { get; set; }

    [JsonPropertyName("wal_config")]
    internal CollectionWALConfig? WalConfig { get; set; }

    [JsonPropertyName("quantization_config")]
    internal CollectionQuantizationConfig? QuantizationConfig { get; set; }
}

internal class CollectionParams
{
    [JsonPropertyName("vectors")]
    internal VectorSettings? VectorParams { get; set; }

    [JsonPropertyName("shard_number")]
    internal int ShardNumber { get; set; }

    [JsonPropertyName("replication_factor")]
    internal int ReplicationFactor { get; set; }

    [JsonPropertyName("write_consistency_factor")]
    internal int WriteConsistencyFactor { get; set; }

    [JsonPropertyName("on_disk_payload")]
    internal bool OnDiskPayload { get; set; }
}

internal class CollectionOptimizerConfig
{
    [JsonPropertyName("deleted_threshold")]
    internal double DeletedThreshold { get; set; }

    [JsonPropertyName("vacuum_min_vector_number")]
    internal int VacuumMinVectorNum { get; set; }

    [JsonPropertyName("default_segment_number")]
    internal int DefaultSegmentNum { get; set; }

    [JsonPropertyName("max_segment_size")]
    internal int MaxSegmentSize { get; set; }

    [JsonPropertyName("memmap_threshold")]
    internal int MemmapThreshold { get; set; }

    [JsonPropertyName("indexing_threshold")]
    internal int IndexingThreshold { get; set; }

    [JsonPropertyName("flush_interval_sec")]
    internal int FlushIntervalSec { get; set; }

    [JsonPropertyName("max_optimization_threads")]
    internal int MaxOptimizationThreads { get; set; }
}

internal class CollectionHnswConfig
{
    [JsonPropertyName("m")]
    internal int NumofEdges { get; set; }

    [JsonPropertyName("ef_construct")]
    internal int NumOfNeighborsIndex { get; set; }

    [JsonPropertyName("full_scan_threshold")]
    internal int FullScanThreshold { get; set; }

    [JsonPropertyName("max_indexing_threads")]
    internal int MaxIndexingThreads { get; set; }

    [JsonPropertyName("on_disk")]
    internal bool IsHNSWOnDisk { get; set; }

    [JsonPropertyName("payload_m")]
    internal int PayloadNumOfEdges { get; set; }
}

internal class CollectionWALConfig
{
    [JsonPropertyName("wal_capacity_mb")]
    internal int WalCapacityMb { get; set; }

    [JsonPropertyName("wal_segments_ahead")]
    internal int WalSegmentsAhead { get; set; }
}

internal class CollectionQuantizationConfig
{
    [JsonPropertyName("scalar")]
    internal ScalarQuantizationConfig? ScalarQuantizationConfig { get; set; }
}

internal class ScalarQuantizationConfig
{
    [JsonPropertyName("type")]
    internal string ScalarType { get; set; } = string.Empty;

    [JsonPropertyName("quantile")]
    internal float Quantile { get; set; }

    [JsonPropertyName("always_ram")]
    internal bool AlwaysRam { get; set; }
}
