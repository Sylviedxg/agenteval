export type ChangeType = 'prompt_update' | 'model_change' | 'tool_update' | 'config_change';

export interface Changelog {
  id: string;
  product_id: string | null;
  experiment_id: string | null;
  change_type: ChangeType;
  title: string;
  description: string | null;
  before_snapshot_id: string | null;
  after_snapshot_id: string | null;
  impact_assessment: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChangelogCreate {
  product_id?: string;
  experiment_id?: string;
  change_type: ChangeType;
  title: string;
  description?: string;
  before_snapshot_id?: string;
  after_snapshot_id?: string;
  impact_assessment?: string;
}
