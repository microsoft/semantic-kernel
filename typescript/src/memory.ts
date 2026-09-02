export interface MemoryRecord {
  id: string;
  embedding: number[];
  metadata?: Record<string, any>;
}

import type { IService } from './types';
import { Logger, ConsoleLogger } from './logger';
import { trace } from '@opentelemetry/api';

export interface VectorMemoryStore extends IService {
  createCollection(name: string): Promise<void>;
  doesCollectionExist(name: string): Promise<boolean>;
  upsert(collection: string, record: MemoryRecord): Promise<void>;
  upsertBatch(collection: string, records: MemoryRecord[]): Promise<void>;
  get(collection: string, id: string): Promise<MemoryRecord | null>;
  getNearestMatches(
    collection: string,
    embedding: number[],
    limit: number
  ): Promise<MemoryRecord[]>;
}

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length && i < b.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  if (!normA || !normB) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

export class InMemoryVectorStore implements VectorMemoryStore {
  private collections = new Map<string, Map<string, MemoryRecord>>();
  private logger: Logger;
  private tracer = trace.getTracer('semantic-kernel');

  constructor(logger: Logger = new ConsoleLogger()) {
    this.logger = logger;
  }

  async createCollection(name: string): Promise<void> {
    if (!this.collections.has(name)) {
      this.collections.set(name, new Map());
    }
  }

  async doesCollectionExist(name: string): Promise<boolean> {
    return this.collections.has(name);
  }

  async upsert(collection: string, record: MemoryRecord): Promise<void> {
    const span = this.tracer.startSpan('Memory.Upsert', {
      attributes: { collection },
    });
    try {
      let col = this.collections.get(collection);
      if (!col) {
        col = new Map();
        this.collections.set(collection, col);
      }
      col.set(record.id, record);
      this.logger.debug('memory upsert', { collection, id: record.id });
    } finally {
      span.end();
    }
  }

  async upsertBatch(collection: string, records: MemoryRecord[]): Promise<void> {
    for (const r of records) {
      await this.upsert(collection, r);
    }
  }

  async get(collection: string, id: string): Promise<MemoryRecord | null> {
    const col = this.collections.get(collection);
    return col?.get(id) ?? null;
  }

  async getNearestMatches(
    collection: string,
    embedding: number[],
    limit: number
  ): Promise<MemoryRecord[]> {
    const col = this.collections.get(collection);
    if (!col) return [];
    const scored: { rec: MemoryRecord; score: number }[] = [];
    for (const rec of col.values()) {
      const score = cosineSimilarity(rec.embedding, embedding);
      scored.push({ rec, score });
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit).map((s) => s.rec);
  }
}
