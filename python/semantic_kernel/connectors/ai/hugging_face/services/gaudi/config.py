from dataclasses import dataclass


@dataclass
class Config:
    """Configuration class for GaudiTextGenerationPipeline"""
    
    # Device configuration
    device: str = "hpu"  # Choices: ["hpu"]
    
    # Model configuration
    model_name_or_path: str = None  # Required
    bf16: bool = False
    max_new_tokens: int = 100
    max_input_tokens: int = 0  # If > 0: pad/truncate to this length, if == 0: truncate to 16, if < 0: use full input
    batch_size: int = 1
    
    # Task configuration
    task: str = None  # Required
    
    # Benchmarking configuration
    warmup: int = 3
    n_iterations: int = 5
    local_rank: int = 0
    
    # Model behavior configuration
    use_kv_cache: bool = False
    use_hpu_graphs: bool = False
    
    # Dataset configuration
    dataset_name: str | None = None
    column_name: str | None = None
    dataset_max_samples: int = -1  # If negative, use whole dataset
    
    # Generation configuration
    do_sample: bool = False
    num_beams: int = 1
    top_k: int | None = None
    penalty_alpha: float | None = None
    trim_logits: bool = False
    seed: int = 27
    num_return_sequences: int = 1
    temperature: float = 1.0
    top_p: float = 1.0
    ignore_eos: bool = True
    
    # Profiling configuration
    profiling_warmup_steps: int = 0
    profiling_steps: int = 0
    profiling_record_shapes: bool = False
    
    # Input configuration
    prompt: list[str] | None = None
    bad_words: list[str] | None = None
    force_words: list[str] | None = None
    
    # Model extensions
    assistant_model: str | None = None
    peft_model: str | None = None
    
    # Authentication
    token: str | None = None
    model_revision: str = "main"
    
    # Optimization configuration
    attn_softmax_bf16: bool = False
    output_dir: str | None = None
    bucket_size: int = -1
    bucket_internal: bool = False
    limit_hpu_graphs: bool = False
    clear_hpu_graphs_cache: bool = False
    show_graphs_count: bool = False
    reuse_cache: bool = False
    verbose_workers: bool = False
    
    # Dynamic prompt configuration
    simulate_dyn_prompt: list[int] | None = None
    reduce_recompile: bool = False
    
    # Template configuration
    use_chat_template: bool = False
    
    # Flash attention configuration
    use_flash_attention: bool = False
    flash_attention_recompute: bool = False
    flash_attention_causal_mask: bool = False
    flash_attention_fast_softmax: bool = False
    
    # Data source configuration
    book_source: bool = False
    
    # Compilation configuration
    torch_compile: bool = False
    
    # Serialization configuration
    const_serialization_path: str | None = None
    
    # Security configuration
    trust_remote_code: bool = False
    
    # Parallelism configuration
    parallel_strategy: str = "none"  # Choices: ["tp", "ep", "none"]
    
    # Input configuration
    input_embeds: bool = False
    run_partial_dataset: bool = False
    
    # Precision configuration
    sdp_on_bf16: bool = False
    
    # Quantization configuration
    save_quantized_model_with_inc: bool = False
    saved_model_path: str = "inc_quantized_model"
    load_quantized_model_with_autogptq: bool = False
    load_quantized_model_with_autoawq: bool = False
    disk_offload: bool = False
    load_quantized_model_with_inc: bool = False
    local_quantized_inc_model_path: str | None = None
    
    # Performance configuration
    attn_batch_split: int = 1
    
    def __post_init__(self):
        """Validate and adjust configuration after initialization."""
        if self.torch_compile:
            self.use_hpu_graphs = False
            
        if not self.use_hpu_graphs:
            self.limit_hpu_graphs = False
            
        if self.use_flash_attention and not self.flash_attention_fast_softmax:
            self.flash_attention_fast_softmax = True
    
    @classmethod
    def from_args(cls, args):
        """Create a Config instance from argparse namespace."""
        return cls(**vars(args))
    
    @classmethod
    def from_dict(cls, config_dict):
        """Create a Config instance from a dictionary."""
        return cls(**config_dict)
    
    def to_dict(self):
        """Convert the config to a dictionary."""
        return {k: v for k, v in self.__dict__.items()}


def create_default_config():
    """Create a default configuration instance."""
    return Config()


def args_to_config(args):
    """Convert an argparse Namespace to a Config object.
    
    Args:
        args: argparse Namespace object
        
    Returns:
        Config object
    """
    return Config.from_args(args)


def dict_to_config(config_dict):
    """Convert a dictionary to a Config object.
    
    Args:
        config_dict: Dictionary containing configuration parameters
        
    Returns:
        Config object
    """
    return Config.from_dict(config_dict) 
