import client from './client';

export interface RecentExperiment {
  id: string;
  name: string;
  status: string;
  overall_score: number | null;
  created_at: string;
}

export interface DashboardStats {
  total_experiments: number;
  total_badcases: number;
  open_badcases: number;
  resolved_badcases: number;
  total_products: number;
  recent_experiments: RecentExperiment[];
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await client.get<DashboardStats>('/dashboard/stats');
  return response.data;
}
