import client from './client';
import type { AxiosResponse } from 'axios';

// 辅助函数
const get = <T>(url: string, config?: { params?: Record<string, unknown> }): Promise<AxiosResponse<T>> => 
  client.get(url, config);
const post = <T>(url: string, data?: unknown): Promise<AxiosResponse<T>> => 
  client.post(url, data);
const put = <T>(url: string, data?: unknown): Promise<AxiosResponse<T>> => 
  client.put(url, data);
const del = (url: string): Promise<AxiosResponse> => 
  client.delete(url);

// 类型定义
export interface MetricCategory {
  id: string;
  name: string;
  code: string;
  level: 'system' | 'collaboration' | 'agent';
  description?: string;
  parent_id?: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  metrics?: MetricDefinition[];
}

export interface MetricDefinition {
  id: string;
  category_id?: string;
  name: string;
  code: string;
  description?: string;
  metric_type: 'process' | 'result';
  scoring_method: 'auto' | 'manual' | 'hybrid';
  data_type: 'number' | 'percentage' | 'duration' | 'boolean' | 'score';
  score_range_min: number;
  score_range_max: number;
  unit?: string;
  evaluation_criteria?: string;
  applicable_node_types?: string[];
  collection_method: 'langfuse' | 'api' | 'manual' | 'computed';
  collection_config?: Record<string, unknown>;
  aggregation_method: 'avg' | 'sum' | 'max' | 'min' | 'last' | 'count';
  weight: number;
  thresholds?: {
    good?: number;
    warning?: number;
    bad?: number;
  };
  sort_order: number;
  is_active: boolean;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
}

export interface Milestone {
  id: string;
  name: string;
  code: string;
  description?: string;
  checkpoint_type: 'entry' | 'process' | 'output' | 'exit';
  applicable_node_types?: string[];
  check_conditions?: Record<string, unknown>;
  related_metrics?: string[];
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MetricSystemOverview {
  system_level: MetricCategory[];
  collaboration_level: MetricCategory[];
  agent_level: MetricCategory[];
  milestones: Milestone[];
  total_metrics: number;
  total_milestones: number;
}

// API 函数

// 分类
export const getCategories = (level?: string) => {
  const params = level ? { level } : {};
  return get<MetricCategory[]>('/metrics/categories', { params });
};

export const createCategory = (data: Partial<MetricCategory>) => {
  return post<MetricCategory>('/metrics/categories', data);
};

export const updateCategory = (id: string, data: Partial<MetricCategory>) => {
  return put<MetricCategory>(`/metrics/categories/${id}`, data);
};

export const deleteCategory = (id: string) => {
  return del(`/metrics/categories/${id}`);
};

// 指标定义
export const getDefinitions = (params?: {
  category_id?: string;
  metric_type?: string;
  scoring_method?: string;
  collection_method?: string;
}) => {
  return get<MetricDefinition[]>('/metrics/definitions', { params });
};

export const getDefinition = (id: string) => {
  return get<MetricDefinition>(`/metrics/definitions/${id}`);
};

export const createDefinition = (data: Partial<MetricDefinition>) => {
  return post<MetricDefinition>('/metrics/definitions', data);
};

export const updateDefinition = (id: string, data: Partial<MetricDefinition>) => {
  return put<MetricDefinition>(`/metrics/definitions/${id}`, data);
};

export const deleteDefinition = (id: string) => {
  return del(`/metrics/definitions/${id}`);
};

// 里程碑
export const getMilestones = (checkpoint_type?: string) => {
  const params = checkpoint_type ? { checkpoint_type } : {};
  return get<Milestone[]>('/metrics/milestones', { params });
};

export const createMilestone = (data: Partial<Milestone>) => {
  return post<Milestone>('/metrics/milestones', data);
};

export const updateMilestone = (id: string, data: Partial<Milestone>) => {
  return put<Milestone>(`/metrics/milestones/${id}`, data);
};

export const deleteMilestone = (id: string) => {
  return del(`/metrics/milestones/${id}`);
};

// 概览
export const getOverview = () => {
  return get<MetricSystemOverview>('/metrics/overview');
};

// 初始化内置指标
export const initBuiltinMetrics = () => {
  return post<{ message: string; initialized: boolean }>('/metrics/init-builtin');
};
