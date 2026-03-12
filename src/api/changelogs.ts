import client from './client';
import type { Changelog, ChangelogCreate } from '../types/changelog';

interface GetChangelogsParams {
  product_id?: string;
  change_type?: string;
}

export async function getChangelogs(params?: GetChangelogsParams): Promise<Changelog[]> {
  const response = await client.get<Changelog[]>('/changelogs', { params });
  return response.data;
}

export async function createChangelog(data: ChangelogCreate): Promise<Changelog> {
  const response = await client.post<Changelog>('/changelogs', data);
  return response.data;
}

export async function getChangelog(id: string): Promise<Changelog> {
  const response = await client.get<Changelog>(`/changelogs/${id}`);
  return response.data;
}
