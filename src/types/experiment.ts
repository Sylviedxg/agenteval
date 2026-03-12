export type ExperimentStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Experiment {
  id: string;
  name: string;
  product_id: string;
  dataset_id: string;
  config_snapshot_id: string | null;
  eval_plan_id: string | null;
  status: ExperimentStatus;
  total_cases: number;
  completed_cases: number;
  overall_score: number | null;
  result_summary: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ExperimentCreate {
  name: string;
  product_id: string;
  dataset_id: string;
  config_snapshot_id?: string;
  eval_plan_id?: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  version: string;
  case_count: number;
  created_at: string;
  updated_at: string;
}

export interface DatasetCreate {
  name: string;
  description?: string;
  version?: string;
}

export interface EvalPlan {
  id: string;
  name: string;
  description: string | null;
  metric_ids: string[] | null;
  node_metric_mapping: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface EvalPlanCreate {
  name: string;
  description?: string;
  metric_ids?: string[];
  node_metric_mapping?: Record<string, unknown>;
}
