export type Severity = 'critical' | 'major' | 'minor';
export type BadCaseStatus = 'open' | 'in_progress' | 'resolved';

export interface BadCase {
  id: string;
  trace_id: string | null;
  case_id: string | null;
  experiment_id: string | null;
  severity: Severity;
  problem_node: string | null;
  problem_type: string | null;
  description: string | null;
  root_cause: string | null;
  fix_suggestion: string | null;
  status: BadCaseStatus;
  created_at: string;
  updated_at: string;
}

export interface BadCaseCreate {
  trace_id?: string;
  case_id?: string;
  experiment_id?: string;
  severity: Severity;
  problem_node?: string;
  problem_type?: string;
  description?: string;
  root_cause?: string;
  fix_suggestion?: string;
}

export interface BadCaseUpdate {
  severity?: Severity;
  problem_node?: string;
  problem_type?: string;
  description?: string;
  root_cause?: string;
  fix_suggestion?: string;
  status?: BadCaseStatus;
}
