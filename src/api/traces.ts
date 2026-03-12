import client from './client';
import type { Trace } from '../types/trace';

export async function getTraces(experimentId?: string): Promise<Trace[]> {
  const params = experimentId ? { experiment_id: experimentId } : {};
  const response = await client.get<Trace[]>('/traces', { params });
  return response.data;
}

export async function getTrace(id: string): Promise<Trace> {
  const response = await client.get<Trace>(`/traces/${id}`);
  return response.data;
}

export async function injectMockTrace(): Promise<{ trace_id: string }> {
  const response = await client.post<{ trace_id: string }>('/mock/inject-trace');
  return response.data;
}
