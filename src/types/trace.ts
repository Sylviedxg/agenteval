export interface TraceEvent {
  event_type: 'tool_call' | 'llm_call' | 'delegate' | 'bubble';
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  tool_output?: Record<string, unknown>;
  model?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  latency_ms?: number;
  input_summary?: string;
  output_summary?: string;
  card_type?: string;
  card_id?: string;
  instruction?: string;
  priority?: number;
  finding_type?: string;
  content?: string;
}

export interface TraceNode {
  node_id: string;
  node_name: string;
  node_type: string;
  card_type?: string;
  status: 'success' | 'failed' | 'running' | 'pending';
  input_summary?: string;
  output_summary?: string;
  latency_ms?: number;
  tokens_used?: number;
  auto_scores?: Record<string, number>;
  manual_scores?: Record<string, number>;
  events?: TraceEvent[];
}

export interface RawTrace {
  query: string;
  final_answer?: string;
  total_latency_ms?: number;
  total_tokens?: number;
  nodes: TraceNode[];
}

export interface Trace {
  id: string;
  experiment_id: string;
  case_id: string;
  status: string;
  raw_trace: RawTrace | null;
  total_tokens: number | null;
  total_latency_ms: number | null;
  created_at: string;
  updated_at: string;
}
