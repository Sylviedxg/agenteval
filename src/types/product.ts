export interface Product {
  id: string;
  name: string;
  description: string | null;
  version: string;
  is_active: boolean;
  config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  name: string;
  description?: string;
  version?: string;
  config?: Record<string, unknown>;
}

export interface ProductUpdate {
  name?: string;
  description?: string;
  version?: string;
  is_active?: boolean;
  config?: Record<string, unknown>;
}
