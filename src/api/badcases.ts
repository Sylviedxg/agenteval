import client from './client';
import type { BadCase, BadCaseCreate, BadCaseUpdate } from '../types/badcase';

interface GetBadCasesParams {
  experiment_id?: string;
  severity?: string;
  status?: string;
}

export async function getBadCases(params?: GetBadCasesParams): Promise<BadCase[]> {
  const response = await client.get<BadCase[]>('/badcases', { params });
  return response.data;
}

export async function createBadCase(data: BadCaseCreate): Promise<BadCase> {
  const response = await client.post<BadCase>('/badcases', data);
  return response.data;
}

export async function getBadCase(id: string): Promise<BadCase> {
  const response = await client.get<BadCase>(`/badcases/${id}`);
  return response.data;
}

export async function updateBadCase(id: string, data: BadCaseUpdate): Promise<BadCase> {
  const response = await client.patch<BadCase>(`/badcases/${id}`, data);
  return response.data;
}

export async function deleteBadCase(id: string): Promise<void> {
  await client.delete(`/badcases/${id}`);
}
