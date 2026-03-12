import client from './client';
import type {
  Experiment,
  ExperimentCreate,
  Dataset,
  DatasetCreate,
  EvalPlan,
  EvalPlanCreate,
} from '../types/experiment';

export async function getExperiments(): Promise<Experiment[]> {
  const response = await client.get<Experiment[]>('/experiments');
  return response.data;
}

export async function createExperiment(data: ExperimentCreate): Promise<Experiment> {
  const response = await client.post<Experiment>('/experiments', data);
  return response.data;
}

export async function getExperiment(id: string): Promise<Experiment> {
  const response = await client.get<Experiment>(`/experiments/${id}`);
  return response.data;
}

export async function getDatasets(): Promise<Dataset[]> {
  const response = await client.get<Dataset[]>('/datasets');
  return response.data;
}

export async function createDataset(data: DatasetCreate): Promise<Dataset> {
  const response = await client.post<Dataset>('/datasets', data);
  return response.data;
}

export async function getEvalPlans(): Promise<EvalPlan[]> {
  const response = await client.get<EvalPlan[]>('/eval-plans');
  return response.data;
}

export async function createEvalPlan(data: EvalPlanCreate): Promise<EvalPlan> {
  const response = await client.post<EvalPlan>('/eval-plans', data);
  return response.data;
}
