/**
 * React Hooks for FAISS Embeddings and PostgreSQL Integration
 * Provides semantic search and data persistence capabilities
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient } from '@/lib/api';

// Embedding and search types
interface EmbeddingVector {
  id: string
  vector: number[]
  metadata: Record<string, any>
  text: string
  timestamp: string
}

interface SearchQuery {
  text: string
  topK?: number
  threshold?: number
  filters?: Record<string, any>
  includeMetadata?: boolean
}

interface SearchResult {
  id: string
  score: number
  text: string
  metadata: Record<string, any>
  distance: number
  timestamp: string
}

interface EmbeddingIndex {
  id: string
  name: string
  description: string
  dimension: number
  totalVectors: number
  status: 'active' | 'building' | 'error'
  createdAt: string
  updatedAt: string
}

interface ContextMemory {
  id: string
  sessionId: string
  content: string
  type: 'conversation' | 'prospect' | 'document' | 'activity'
  embedding: number[]
  metadata: Record<string, any>
  relevanceScore?: number
  createdAt: string
}

interface UseEmbeddingSearchReturn {
  search: (query: SearchQuery) => Promise<SearchResult[]>
  addVector: (text: string, metadata: Record<string, any>) => Promise<EmbeddingVector>
  deleteVector: (id: string) => Promise<void>
  getIndices: () => Promise<EmbeddingIndex[]>
  buildIndex: (name: string, documents: Array<{ text: string; metadata: Record<string, any> }>) => Promise<EmbeddingIndex>
  isLoading: boolean
  error: string | null
}

interface UseContextMemoryReturn {
  memories: ContextMemory[]
  addMemory: (content: string, type: ContextMemory['type'], metadata?: Record<string, any>) => Promise<ContextMemory>
  searchMemories: (query: string, filters?: Record<string, any>) => Promise<ContextMemory[]>
  getRelevantContext: (query: string, maxTokens?: number) => Promise<string>
  clearMemories: (sessionId?: string) => Promise<void>
  isLoading: boolean
  error: string | null
}

interface UseDataPersistenceReturn {
  saveData: (table: string, data: Record<string, any>) => Promise<{ id: string }>
  updateData: (table: string, id: string, updates: Record<string, any>) => Promise<void>
  deleteData: (table: string, id: string) => Promise<void>
  queryData: (table: string, filters?: Record<string, any>, orderBy?: string, limit?: number) => Promise<any[]>
  executeQuery: (sql: string, params?: any[]) => Promise<any[]>
  isLoading: boolean
  error: string | null
}

// FAISS Embeddings API client
class EmbeddingsApi {
  constructor(private apiClient: any) {}

  async search(query: SearchQuery): Promise<SearchResult[]> {
    const response = await this.apiClient.post('/api/embeddings/search', query);
    return response.data;
  }

  async addVector(text: string, metadata: Record<string, any>): Promise<EmbeddingVector> {
    const response = await this.apiClient.post('/api/embeddings/add', { text, metadata });
    return response.data;
  }

  async deleteVector(id: string): Promise<void> {
    await this.apiClient.delete(`/api/embeddings/${id}`);
  }

  async getIndices(): Promise<EmbeddingIndex[]> {
    const response = await this.apiClient.get('/api/embeddings/indices');
    return response.data;
  }

  async buildIndex(name: string, documents: Array<{ text: string; metadata: Record<string, any> }>): Promise<EmbeddingIndex> {
    const response = await this.apiClient.post('/api/embeddings/indices', { name, documents });
    return response.data;
  }

  async getEmbedding(text: string): Promise<number[]> {
    const response = await this.apiClient.post('/api/embeddings/encode', { text });
    return response.data.embedding;
  }
}

// Context Memory API client
class ContextMemoryApi {
  constructor(private apiClient: any) {}

  async getMemories(sessionId: string): Promise<ContextMemory[]> {
    const response = await this.apiClient.get(`/api/memory/${sessionId}`);
    return response.data;
  }

  async addMemory(sessionId: string, content: string, type: ContextMemory['type'], metadata?: Record<string, any>): Promise<ContextMemory> {
    const response = await this.apiClient.post('/api/memory', {
      sessionId,
      content,
      type,
      metadata: metadata || {}
    });
    return response.data;
  }

  async searchMemories(sessionId: string, query: string, filters?: Record<string, any>): Promise<ContextMemory[]> {
    const response = await this.apiClient.post('/api/memory/search', {
      sessionId,
      query,
      filters: filters || {}
    });
    return response.data;
  }

  async getRelevantContext(sessionId: string, query: string, maxTokens = 2000): Promise<string> {
    const response = await this.apiClient.post('/api/memory/context', {
      sessionId,
      query,
      maxTokens
    });
    return response.data.context;
  }

  async clearMemories(sessionId?: string): Promise<void> {
    if (sessionId) {
      await this.apiClient.delete(`/api/memory/${sessionId}`);
    } else {
      await this.apiClient.delete('/api/memory');
    }
  }
}

// PostgreSQL Data API client
class DataPersistenceApi {
  constructor(private apiClient: any) {}

  async saveData(table: string, data: Record<string, any>): Promise<{ id: string }> {
    const response = await this.apiClient.post(`/api/data/${table}`, data);
    return response.data;
  }

  async updateData(table: string, id: string, updates: Record<string, any>): Promise<void> {
    await this.apiClient.put(`/api/data/${table}/${id}`, updates);
  }

  async deleteData(table: string, id: string): Promise<void> {
    await this.apiClient.delete(`/api/data/${table}/${id}`);
  }

  async queryData(table: string, filters?: Record<string, any>, orderBy?: string, limit?: number): Promise<any[]> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        params.append(`filter[${key}]`, String(value));
      });
    }
    if (orderBy) params.append('orderBy', orderBy);
    if (limit) params.append('limit', String(limit));

    const response = await this.apiClient.get(`/api/data/${table}?${params}`);
    return response.data;
  }

  async executeQuery(sql: string, params?: any[]): Promise<any[]> {
    const response = await this.apiClient.post('/api/data/query', { sql, params });
    return response.data;
  }
}

// Main embedding search hook
export const useEmbeddingSearch = (indexName?: string): UseEmbeddingSearchReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const embeddingsApi = new EmbeddingsApi(apiClient);

  const search = useCallback(async (query: SearchQuery): Promise<SearchResult[]> => {
    try {
      setIsLoading(true);
      setError(null);

      const results = await embeddingsApi.search({
        ...query,
        topK: query.topK || 10,
        threshold: query.threshold || 0.3,
        includeMetadata: query.includeMetadata !== false
      });

      return results;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to search embeddings';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [embeddingsApi]);

  const addVector = useCallback(async (text: string, metadata: Record<string, any>): Promise<EmbeddingVector> => {
    try {
      setIsLoading(true);
      setError(null);

      const vector = await embeddingsApi.addVector(text, metadata);
      return vector;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to add vector';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [embeddingsApi]);

  const deleteVector = useCallback(async (id: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      await embeddingsApi.deleteVector(id);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete vector';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [embeddingsApi]);

  const getIndices = useCallback(async (): Promise<EmbeddingIndex[]> => {
    try {
      setIsLoading(true);
      setError(null);

      const indices = await embeddingsApi.getIndices();
      return indices;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get indices';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [embeddingsApi]);

  const buildIndex = useCallback(async (name: string, documents: Array<{ text: string; metadata: Record<string, any> }>): Promise<EmbeddingIndex> => {
    try {
      setIsLoading(true);
      setError(null);

      const index = await embeddingsApi.buildIndex(name, documents);
      return index;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to build index';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [embeddingsApi]);

  return {
    search,
    addVector,
    deleteVector,
    getIndices,
    buildIndex,
    isLoading,
    error
  };
};

// Context memory hook for maintaining conversation context
export const useContextMemory = (sessionId: string): UseContextMemoryReturn => {
  const [memories, setMemories] = useState<ContextMemory[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const memoryApi = new ContextMemoryApi(apiClient);

  // Load memories for session
  useEffect(() => {
    const loadMemories = async () => {
      try {
        setIsLoading(true);
        const sessionMemories = await memoryApi.getMemories(sessionId);
        setMemories(sessionMemories);
      } catch (err: any) {
        setError(err.message || 'Failed to load memories');
      } finally {
        setIsLoading(false);
      }
    };

    if (sessionId) {
      loadMemories();
    }
  }, [sessionId, memoryApi]);

  const addMemory = useCallback(async (content: string, type: ContextMemory['type'], metadata?: Record<string, any>): Promise<ContextMemory> => {
    try {
      setIsLoading(true);
      setError(null);

      const memory = await memoryApi.addMemory(sessionId, content, type, metadata);
      setMemories(prev => [memory, ...prev]);
      return memory;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to add memory';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, memoryApi]);

  const searchMemories = useCallback(async (query: string, filters?: Record<string, any>): Promise<ContextMemory[]> => {
    try {
      setIsLoading(true);
      setError(null);

      const results = await memoryApi.searchMemories(sessionId, query, filters);
      return results;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to search memories';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, memoryApi]);

  const getRelevantContext = useCallback(async (query: string, maxTokens = 2000): Promise<string> => {
    try {
      setIsLoading(true);
      setError(null);

      const context = await memoryApi.getRelevantContext(sessionId, query, maxTokens);
      return context;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get relevant context';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, memoryApi]);

  const clearMemories = useCallback(async (targetSessionId?: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      await memoryApi.clearMemories(targetSessionId || sessionId);
      if (!targetSessionId || targetSessionId === sessionId) {
        setMemories([]);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to clear memories';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, memoryApi]);

  return {
    memories,
    addMemory,
    searchMemories,
    getRelevantContext,
    clearMemories,
    isLoading,
    error
  };
};

// PostgreSQL data persistence hook
export const useDataPersistence = (): UseDataPersistenceReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dataApi = new DataPersistenceApi(apiClient);

  const saveData = useCallback(async (table: string, data: Record<string, any>): Promise<{ id: string }> => {
    try {
      setIsLoading(true);
      setError(null);

      const result = await dataApi.saveData(table, data);
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to save data';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [dataApi]);

  const updateData = useCallback(async (table: string, id: string, updates: Record<string, any>): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      await dataApi.updateData(table, id, updates);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to update data';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [dataApi]);

  const deleteData = useCallback(async (table: string, id: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      await dataApi.deleteData(table, id);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to delete data';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [dataApi]);

  const queryData = useCallback(async (table: string, filters?: Record<string, any>, orderBy?: string, limit?: number): Promise<any[]> => {
    try {
      setIsLoading(true);
      setError(null);

      const results = await dataApi.queryData(table, filters, orderBy, limit);
      return results;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to query data';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [dataApi]);

  const executeQuery = useCallback(async (sql: string, params?: any[]): Promise<any[]> => {
    try {
      setIsLoading(true);
      setError(null);

      const results = await dataApi.executeQuery(sql, params);
      return results;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to execute query';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [dataApi]);

  return {
    saveData,
    updateData,
    deleteData,
    queryData,
    executeQuery,
    isLoading,
    error
  };
};