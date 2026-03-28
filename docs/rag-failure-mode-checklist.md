# RAG Failure Mode Checklist for Semantic Kernel

**Author**: Dr. Rajan Prasad Tripathi | AUT AI Innovation Lab
**Reference**: [Semantic Kernel Issue #13581](https://github.com/microsoft/semantic-kernel/issues/13581)
**Based on**: WFGY 16-Problem Map

---

## Overview

This checklist provides a systematic taxonomy of RAG (Retrieval-Augmented Generation) failure modes, mapped to Semantic Kernel components. It is designed to help developers debug their RAG pipelines and choose the right knobs to turn when answers look wrong.

---

## The 16 RAG Failure Modes

### Category 1: Retrieval Failures

#### 1. Retrieval Collapse
**Symptoms**: Irrelevant chunks returned; model hallucinates without evidence

**Semantic Kernel Components**:
- `TextSearchPlugin`
- `VectorStore`
- `ITextEmbeddingGenerationService`

**Detection**:
```python
from ragas.metrics import context_precision
# context_precision < 0.3 indicates collapse
```

**Fixes**:
- Check embedding model compatibility with your domain
- Verify query transformation is applied
- Increase `top_k` or adjust `score_threshold`
- Check for embedding dimension mismatch

---

#### 2. Semantic vs Embedding Mismatch
**Symptoms**: Semantically similar content not retrieved; exact keyword matches preferred

**Semantic Kernel Components**:
- `ITextEmbeddingGenerationService`
- Embedding model selection

**Detection**:
- Compare cosine similarity scores for known similar/different pairs
- Test with paraphrased queries vs exact keyword queries

**Fixes**:
- Switch to domain-specific embeddings (e.g., medical embeddings for healthcare)
- Add keyword hybrid search alongside semantic search
- Fine-tune embeddings on domain corpus

---

#### 3. Chunk Drift
**Symptoms**: Retrieved chunks lack coherent context; information spread across chunks

**Semantic Kernel Components**:
- `TextChunker`
- Chunking strategy configuration

**Detection**:
- Analyze chunk boundaries for mid-sentence splits
- Check if multi-hop reasoning questions fail

**Fixes**:
- Implement semantic chunking (by paragraphs, not character count)
- Add chunk overlap (typically 10-20%)
- Use parent-child chunking for context

---

#### 4. Query-Document Language Mismatch
**Symptoms**: Cross-lingual queries fail; documents in one language not retrieved by queries in another

**Semantic Kernel Components**:
- `ITextEmbeddingGenerationService`
- Query translation pipeline

**Detection**:
```python
# Test with translated queries
# If English query returns Chinese docs but Chinese query doesn't
# There's a language mismatch
```

**Fixes**:
- Use multilingual embeddings (e.g., `paraphrase-multilingual-mpnet-base-v2`)
- Implement query translation before retrieval
- Create separate indices per language with cross-lingual mapping

---

### Category 2: Context Assembly Failures

#### 5. Context Window Overflow
**Symptoms**: Important information truncated; later chunks ignored

**Semantic Kernel Components**:
- `ChatHistoryPromptTemplate`
- Token counting utilities

**Detection**:
- Log token counts before/after context assembly
- Check if retrieval results are consistently truncated

**Fixes**:
- Implement relevance-based re-ranking before truncation
- Use map-reduce pattern for long contexts
- Summarize chunks before assembly

---

#### 6. Context Order Bias
**Symptoms**: Information at the beginning/end of context dominates; middle content ignored

**Semantic Kernel Components**:
- `ChatHistoryPromptTemplate`
- Context ordering logic

**Detection**:
- Test with same content in different orders
- Compare model responses for order sensitivity

**Fixes**:
- Place most relevant chunks at beginning AND end
- Implement chunk-level attention visualization
- Use chain-of-thought prompting to force comprehensive analysis

---

#### 7. Missing Source Attribution
**Symptoms**: Model claims facts without citing sources; hallucinations undetected

**Semantic Kernel Components**:
- `KernelFunction` with metadata
- Response post-processing

**Detection**:
```python
from ragas.metrics import faithfulness
# faithfulness < 0.7 indicates attribution issues
```

**Fixes**:
- Require citations in the prompt template
- Add source metadata to each chunk
- Post-process responses to validate citations

---

### Category 3: Generation Failures

#### 8. Hallucination
**Symptoms**: Model generates content not in retrieved context

**Semantic Kernel Components**:
- `IChatCompletionService`
- Prompt template engineering

**Detection**:
```python
from ragas.metrics import faithfulness
# faithfulness < 0.5 indicates hallucination
```

**Fixes**:
- Strengthen system prompt: "Only answer based on provided context"
- Implement groundedness scoring
- Use retrieval-augmented faithfulness training

---

#### 9. Answer Relevance Drift
**Symptoms**: Model answers a different question than asked; tangential responses

**Semantic Kernel Components**:
- `IChatCompletionService`
- `ChatHistoryPromptTemplate`

**Detection**:
```python
from ragas.metrics import answer_relevancy
# answer_relevancy < 0.6 indicates drift
```

**Fixes**:
- Add question restatement in prompt
- Implement query-focused prompting
- Use answer relevancy as a generation filter

---

#### 10. Format Inconsistency
**Symptoms**: Model ignores requested output format; JSON malformed, lists inconsistent

**Semantic Kernel Components**:
- `PromptTemplateConfig`
- Output parsing

**Detection**:
- Parse output and check against expected schema
- Log format compliance rate

**Fixes**:
- Use structured output with function calling
- Provide few-shot examples of correct format
- Implement format validation and retry

---

### Category 4: Healthcare-Specific Failures

#### 11. PHI/PII Leakage
**Symptoms**: Protected health information exposed in responses

**Semantic Kernel Components**:
- Input/output filtering
- `IPromptFilter` for PII detection

**Detection**:
- Scan outputs for PHI patterns (SSN, MRN, names)
- Log potential PII exposures

**Fixes**:
- Implement PHI detection filter
- Redact sensitive data before retrieval
- Add PHI audit logging

**Multilingual Consideration**:
- PHI patterns differ across languages:
  - English: SSN (XXX-XX-XXXX), MRN
  - Chinese: 身份证号, 姓名
  - Arabic: الرقم الوطني, الاسم

---

#### 12. Medical Terminology Inconsistency
**Symptoms**: Incorrect medical terminology; inconsistent disease/drug names

**Semantic Kernel Components**:
- Medical entity recognition
- Terminology normalization

**Detection**:
- Validate against medical terminology databases (UMLS, SNOMED)
- Check cross-lingual terminology consistency

**Fixes**:
- Implement medical entity linking
- Add terminology normalization layer
- Use medical-specific embeddings

---

#### 13. Outdated Clinical Guidelines
**Symptoms**: Model recommends superseded treatments; references old guidelines

**Semantic Kernel Components**:
- `VectorStore` with temporal metadata
- Document freshness scoring

**Detection**:
- Compare recommendations against current guidelines
- Check document dates in context

**Fixes**:
- Add recency weighting to retrieval
- Implement guideline version tracking
- Flag outdated recommendations

---

### Category 5: Multilingual Failures

#### 14. Script Mismatch
**Symptoms**: Latin script queries retrieve CJK documents poorly; RTL text corrupted

**Semantic Kernel Components**:
- `ITextEmbeddingGenerationService`
- Text preprocessing

**Detection**:
- Test retrieval quality across scripts
- Check embedding similarity for cross-script pairs

**Fixes**:
- Use script-aware text preprocessing
- Implement script detection and routing
- Consider script-specific embeddings

---

#### 15. Embedding Density Variance
**Symptoms**: Some languages have lower retrieval quality; inconsistent performance across languages

**Semantic Kernel Components**:
- `ITextEmbeddingGenerationService`
- Embedding model selection

**Detection**:
```python
# Compare context_recall across languages
# Significant variance indicates density issues
```

**Fixes**:
- Adjust score thresholds per language
- Use language-specific embedding models
- Apply language-aware chunking (different sizes for different scripts)

---

#### 16. Cross-Lingual Semantic Drift
**Symptoms**: Translated queries return different results than native queries; meaning lost in translation

**Semantic Kernel Components**:
- Query translation pipeline
- Cross-lingual retrieval

**Detection**:
- Compare results for query in original vs translated form
- Measure semantic similarity of retrieved sets

**Fixes**:
- Use multilingual embeddings that preserve cross-lingual semantics
- Implement query expansion in both languages
- Consider RAGAS `adapt_prompts()` for multilingual evaluation

---

## Quick Reference Table

| # | Failure Mode | Primary Component | Detection Metric | Quick Fix |
|---|-------------|-------------------|------------------|-----------|
| 1 | Retrieval Collapse | TextSearchPlugin | context_precision < 0.3 | Increase top_k |
| 2 | Semantic Mismatch | EmbeddingService | Similarity analysis | Switch embeddings |
| 3 | Chunk Drift | TextChunker | Mid-sentence splits | Add overlap |
| 4 | Language Mismatch | EmbeddingService | Cross-lingual test | Multilingual embeddings |
| 5 | Context Overflow | PromptTemplate | Token count | Re-ranking |
| 6 | Order Bias | PromptTemplate | Order sensitivity test | Distribute relevant |
| 7 | Missing Attribution | KernelFunction | faithfulness < 0.7 | Require citations |
| 8 | Hallucination | ChatCompletion | faithfulness < 0.5 | Strengthen prompt |
| 9 | Relevance Drift | ChatCompletion | answer_relevancy < 0.6 | Query restatement |
| 10 | Format Inconsistency | PromptTemplate | Schema validation | Structured output |
| 11 | PHI Leakage | PromptFilter | PHI scan | Detection filter |
| 12 | Terminology Error | Entity linking | UMLS validation | Normalization |
| 13 | Outdated Guidelines | VectorStore | Date check | Recency weighting |
| 14 | Script Mismatch | EmbeddingService | Cross-script test | Script detection |
| 15 | Density Variance | EmbeddingService | Per-language metrics | Language-specific |
| 16 | Semantic Drift | Translation | Translation test | Multilingual embed |

---

## Implementation Example

```csharp
// C# Example: RAG Failure Detection in Semantic Kernel

public class RAGFailureDetector
{
    private readonly Kernel _kernel;

    public async Task<RAGDiagnostics> DiagnoseAsync(string query, string response, List<string> contexts)
    {
        var diagnostics = new RAGDiagnostics();

        // Check 1: Retrieval Collapse
        diagnostics.ContextPrecision = await EvaluateContextPrecision(query, contexts);

        // Check 2: Hallucination
        diagnostics.Faithfulness = await EvaluateFaithfulness(response, contexts);

        // Check 3: Answer Relevance
        diagnostics.AnswerRelevancy = await EvaluateAnswerRelevancy(query, response);

        // Check 4: PHI Detection (healthcare)
        diagnostics.PHIDetected = DetectPHI(response);

        // Determine primary failure
        diagnostics.PrimaryFailure = DeterminePrimaryFailure(diagnostics);

        return diagnostics;
    }

    private string DeterminePrimaryFailure(RAGDiagnostics d)
    {
        if (d.ContextPrecision < 0.3) return "Retrieval Collapse";
        if (d.Faithfulness < 0.5) return "Hallucination";
        if (d.AnswerRelevancy < 0.6) return "Answer Relevance Drift";
        if (d.PHIDetected) return "PHI Leakage";
        return "None Detected";
    }
}
```

---

## References

1. WFGY 16-Problem Map: https://github.com/onestardao/WFGY/blob/main/ProblemMap/README.md
2. RAGAS Evaluation Framework: https://github.com/vibrantlabsai/ragas
3. RAGAS Multilingual Fix (PR #2651): https://github.com/vibrantlabsai/ragas/pull/2651
4. SOAS RAG Evaluation Benchmark: https://github.com/rajantripathi/soas-rag-evaluation
5. DeepEval Multilingual Proposal: https://github.com/confident-ai/deepeval/issues/2578

---

**Author**: Dr. Rajan Prasad Tripathi
**Affiliation**: Director, AUT AI Innovation Lab
**GitHub**: [@rajantripathi](https://github.com/rajantripathi)
**Research Focus**: Multilingual RAG, Healthcare AI, Evaluation Frameworks
