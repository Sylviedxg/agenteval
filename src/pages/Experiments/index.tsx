import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Table, Button, Modal, Form, Input, Select, message, Tag, Space } from 'antd';
import { PlusOutlined, EyeOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  getExperiments,
  createExperiment,
  getDatasets,
  createDataset,
  getEvalPlans,
  createEvalPlan,
} from '../../api/experiments';
import { getProducts } from '../../api/products';
import type { Experiment, ExperimentCreate, ExperimentStatus, DatasetCreate, EvalPlanCreate } from '../../types/experiment';

const statusConfig: Record<ExperimentStatus, { color: string; text: string }> = {
  pending: { color: 'default', text: '待执行' },
  running: { color: 'processing', text: '运行中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
};

export default function Experiments() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDatasetModalOpen, setIsDatasetModalOpen] = useState(false);
  const [isEvalPlanModalOpen, setIsEvalPlanModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [datasetForm] = Form.useForm();
  const [evalPlanForm] = Form.useForm();

  const { data: experiments, isLoading } = useQuery({
    queryKey: ['experiments'],
    queryFn: getExperiments,
  });

  const { data: products } = useQuery({
    queryKey: ['products'],
    queryFn: getProducts,
  });

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: getDatasets,
  });

  const { data: evalPlans } = useQuery({
    queryKey: ['evalPlans'],
    queryFn: getEvalPlans,
  });

  const createExperimentMutation = useMutation({
    mutationFn: createExperiment,
    onSuccess: () => {
      message.success('实验创建成功');
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
      setIsModalOpen(false);
      form.resetFields();
    },
    onError: () => {
      message.error('实验创建失败');
    },
  });

  const createDatasetMutation = useMutation({
    mutationFn: createDataset,
    onSuccess: (newDataset) => {
      message.success('评测集创建成功');
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      setIsDatasetModalOpen(false);
      datasetForm.resetFields();
      form.setFieldValue('dataset_id', newDataset.id);
    },
    onError: () => {
      message.error('评测集创建失败');
    },
  });

  const createEvalPlanMutation = useMutation({
    mutationFn: createEvalPlan,
    onSuccess: (newEvalPlan) => {
      message.success('评测方案创建成功');
      queryClient.invalidateQueries({ queryKey: ['evalPlans'] });
      setIsEvalPlanModalOpen(false);
      evalPlanForm.resetFields();
      form.setFieldValue('eval_plan_id', newEvalPlan.id);
    },
    onError: () => {
      message.error('评测方案创建失败');
    },
  });

  const handleCreateExperiment = (values: ExperimentCreate) => {
    createExperimentMutation.mutate(values);
  };

  const handleCreateDataset = (values: DatasetCreate) => {
    createDatasetMutation.mutate(values);
  };

  const handleCreateEvalPlan = (values: EvalPlanCreate) => {
    createEvalPlanMutation.mutate(values);
  };

  const columns: ColumnsType<Experiment> = [
    {
      title: '实验名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record) => (
        <a onClick={() => navigate(`/experiments/${record.id}`)} className="text-blue-400 hover:text-blue-300">
          {name}
        </a>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: ExperimentStatus) => (
        <Tag color={statusConfig[status]?.color || 'default'}>
          {statusConfig[status]?.text || status}
        </Tag>
      ),
    },
    {
      title: '总 Case 数',
      dataIndex: 'total_cases',
      key: 'total_cases',
    },
    {
      title: '完成数',
      dataIndex: 'completed_cases',
      key: 'completed_cases',
    },
    {
      title: '综合评分',
      dataIndex: 'overall_score',
      key: 'overall_score',
      render: (score: number | null) => (score !== null ? score.toFixed(2) : '—'),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/experiments/${record.id}`)}
          >
            详情
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-white text-xl font-semibold">实验</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          新建实验
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={experiments}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="新建实验"
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          form.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateExperiment}>
          <Form.Item
            name="name"
            label="实验名称"
            rules={[{ required: true, message: '请输入实验名称' }]}
          >
            <Input placeholder="请输入实验名称" />
          </Form.Item>

          <Form.Item
            name="product_id"
            label="选择产品"
            rules={[{ required: true, message: '请选择产品' }]}
          >
            <Select placeholder="请选择产品">
              {products?.map((product) => (
                <Select.Option key={product.id} value={product.id}>
                  {product.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="选择评测集" required>
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item
                name="dataset_id"
                noStyle
                rules={[{ required: true, message: '请选择评测集' }]}
              >
                <Select placeholder="请选择评测集" style={{ width: 'calc(100% - 80px)' }}>
                  {datasets?.map((dataset) => (
                    <Select.Option key={dataset.id} value={dataset.id}>
                      {dataset.name} (v{dataset.version})
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Button onClick={() => setIsDatasetModalOpen(true)}>+ 新建</Button>
            </Space.Compact>
          </Form.Item>

          <Form.Item label="选择评测方案">
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item name="eval_plan_id" noStyle>
                <Select placeholder="请选择评测方案（可选）" style={{ width: 'calc(100% - 80px)' }} allowClear>
                  {evalPlans?.map((plan) => (
                    <Select.Option key={plan.id} value={plan.id}>
                      {plan.name}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Button onClick={() => setIsEvalPlanModalOpen(true)}>+ 新建</Button>
            </Space.Compact>
          </Form.Item>

          <Form.Item className="mb-0 flex justify-end">
            <Space>
              <Button onClick={() => { setIsModalOpen(false); form.resetFields(); }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={createExperimentMutation.isPending}>
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新建评测集"
        open={isDatasetModalOpen}
        onCancel={() => { setIsDatasetModalOpen(false); datasetForm.resetFields(); }}
        footer={null}
      >
        <Form form={datasetForm} layout="vertical" onFinish={handleCreateDataset}>
          <Form.Item
            name="name"
            label="评测集名称"
            rules={[{ required: true, message: '请输入评测集名称' }]}
          >
            <Input placeholder="请输入评测集名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入描述" rows={2} />
          </Form.Item>
          <Form.Item name="version" label="版本" initialValue="1.0.0">
            <Input placeholder="请输入版本号" />
          </Form.Item>
          <Form.Item className="mb-0 flex justify-end">
            <Space>
              <Button onClick={() => { setIsDatasetModalOpen(false); datasetForm.resetFields(); }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={createDatasetMutation.isPending}>
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新建评测方案"
        open={isEvalPlanModalOpen}
        onCancel={() => { setIsEvalPlanModalOpen(false); evalPlanForm.resetFields(); }}
        footer={null}
      >
        <Form form={evalPlanForm} layout="vertical" onFinish={handleCreateEvalPlan}>
          <Form.Item
            name="name"
            label="方案名称"
            rules={[{ required: true, message: '请输入方案名称' }]}
          >
            <Input placeholder="请输入方案名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入描述" rows={2} />
          </Form.Item>
          <Form.Item className="mb-0 flex justify-end">
            <Space>
              <Button onClick={() => { setIsEvalPlanModalOpen(false); evalPlanForm.resetFields(); }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={createEvalPlanMutation.isPending}>
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
