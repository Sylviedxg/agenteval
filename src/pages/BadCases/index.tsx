import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Table, Button, Modal, Form, Input, Select, message, Tag, Space, Drawer, Popconfirm
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getBadCases, createBadCase, updateBadCase, deleteBadCase } from '../../api/badcases';
import type { BadCase, BadCaseCreate, BadCaseUpdate, Severity, BadCaseStatus } from '../../types/badcase';

const severityConfig: Record<Severity, { color: string; text: string }> = {
  critical: { color: 'red', text: '严重' },
  major: { color: 'orange', text: '重要' },
  minor: { color: 'gold', text: '轻微' },
};

const statusConfig: Record<BadCaseStatus, { color: string; text: string }> = {
  open: { color: 'red', text: '待处理' },
  in_progress: { color: 'blue', text: '处理中' },
  resolved: { color: 'green', text: '已解决' },
};

export default function BadCases() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedBadCase, setSelectedBadCase] = useState<BadCase | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const [filters, setFilters] = useState<{ severity?: string; status?: string }>({});

  const { data: badcases, isLoading } = useQuery({
    queryKey: ['badcases', filters],
    queryFn: () => getBadCases(filters),
  });

  const createMutation = useMutation({
    mutationFn: createBadCase,
    onSuccess: () => {
      message.success('BadCase 创建成功');
      queryClient.invalidateQueries({ queryKey: ['badcases'] });
      setIsModalOpen(false);
      form.resetFields();
    },
    onError: () => {
      message.error('BadCase 创建失败');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: BadCaseUpdate }) => updateBadCase(id, data),
    onSuccess: () => {
      message.success('保存成功');
      queryClient.invalidateQueries({ queryKey: ['badcases'] });
      setIsDrawerOpen(false);
      setSelectedBadCase(null);
    },
    onError: () => {
      message.error('保存失败');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteBadCase,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['badcases'] });
      setIsDrawerOpen(false);
      setSelectedBadCase(null);
    },
    onError: () => {
      message.error('删除失败');
    },
  });

  const handleCreate = (values: BadCaseCreate) => {
    createMutation.mutate(values);
  };

  const handleEdit = (record: BadCase) => {
    setSelectedBadCase(record);
    editForm.setFieldsValue(record);
    setIsDrawerOpen(true);
  };

  const handleSave = () => {
    editForm.validateFields().then((values) => {
      if (selectedBadCase) {
        updateMutation.mutate({ id: selectedBadCase.id, data: values });
      }
    });
  };

  const handleDelete = () => {
    if (selectedBadCase) {
      deleteMutation.mutate(selectedBadCase.id);
    }
  };

  const columns: ColumnsType<BadCase> = [
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: Severity) => (
        <Tag color={severityConfig[severity]?.color || 'default'}>
          {severityConfig[severity]?.text || severity}
        </Tag>
      ),
    },
    {
      title: '问题节点',
      dataIndex: 'problem_node',
      key: 'problem_node',
      width: 120,
      render: (text: string | null) => text || '—',
    },
    {
      title: '问题类型',
      dataIndex: 'problem_type',
      key: 'problem_type',
      width: 120,
      render: (text: string | null) => text || '—',
    },
    {
      title: '问题描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string | null) => text ? (text.length > 50 ? text.slice(0, 50) + '...' : text) : '—',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: BadCaseStatus) => (
        <Tag color={statusConfig[status]?.color || 'default'}>
          {statusConfig[status]?.text || status}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button type="text" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
          编辑
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-white text-xl font-semibold">BadCase</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          新建 BadCase
        </Button>
      </div>

      <div className="flex gap-4 mb-4">
        <Select
          placeholder="严重程度"
          allowClear
          style={{ width: 120 }}
          onChange={(value) => setFilters((prev) => ({ ...prev, severity: value }))}
          options={[
            { value: 'critical', label: '严重' },
            { value: 'major', label: '重要' },
            { value: 'minor', label: '轻微' },
          ]}
        />
        <Select
          placeholder="状态"
          allowClear
          style={{ width: 120 }}
          onChange={(value) => setFilters((prev) => ({ ...prev, status: value }))}
          options={[
            { value: 'open', label: '待处理' },
            { value: 'in_progress', label: '处理中' },
            { value: 'resolved', label: '已解决' },
          ]}
        />
      </div>

      <Table
        columns={columns}
        dataSource={badcases}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="新建 BadCase"
        open={isModalOpen}
        onCancel={() => { setIsModalOpen(false); form.resetFields(); }}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="severity"
            label="严重程度"
            rules={[{ required: true, message: '请选择严重程度' }]}
            initialValue="minor"
          >
            <Select>
              <Select.Option value="critical">严重</Select.Option>
              <Select.Option value="major">重要</Select.Option>
              <Select.Option value="minor">轻微</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="problem_node" label="问题节点">
            <Input placeholder="请输入问题节点" />
          </Form.Item>
          <Form.Item name="problem_type" label="问题类型">
            <Input placeholder="请输入问题类型" />
          </Form.Item>
          <Form.Item name="description" label="问题描述">
            <Input.TextArea placeholder="请输入问题描述" rows={3} />
          </Form.Item>
          <Form.Item className="mb-0 flex justify-end">
            <Space>
              <Button onClick={() => { setIsModalOpen(false); form.resetFields(); }}>取消</Button>
              <Button type="primary" htmlType="submit" loading={createMutation.isPending}>创建</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        title="BadCase 详情"
        placement="right"
        size="large"
        onClose={() => { setIsDrawerOpen(false); setSelectedBadCase(null); }}
        open={isDrawerOpen}
        extra={
          <Space>
            <Popconfirm
              title="确认删除"
              description="确定要删除这个 BadCase 吗？"
              onConfirm={handleDelete}
              okText="确认"
              cancelText="取消"
            >
              <Button danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
            <Button type="primary" onClick={handleSave} loading={updateMutation.isPending}>
              保存
            </Button>
          </Space>
        }
      >
        <Form form={editForm} layout="vertical">
          <div className="mb-4 font-semibold text-gray-300">基本信息</div>
          <Form.Item name="severity" label="严重程度">
            <Select>
              <Select.Option value="critical">严重</Select.Option>
              <Select.Option value="major">重要</Select.Option>
              <Select.Option value="minor">轻微</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select>
              <Select.Option value="open">待处理</Select.Option>
              <Select.Option value="in_progress">处理中</Select.Option>
              <Select.Option value="resolved">已解决</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="problem_node" label="问题节点">
            <Input placeholder="请输入问题节点" />
          </Form.Item>
          <Form.Item name="problem_type" label="问题类型">
            <Input placeholder="请输入问题类型" />
          </Form.Item>

          <div className="mb-4 mt-6 font-semibold text-gray-300">问题分析</div>
          <Form.Item name="description" label="问题描述">
            <Input.TextArea placeholder="请输入问题描述" rows={3} />
          </Form.Item>
          <Form.Item name="root_cause" label="根因分析">
            <Input.TextArea placeholder="请输入根因分析" rows={3} />
          </Form.Item>
          <Form.Item name="fix_suggestion" label="修复建议">
            <Input.TextArea placeholder="请输入修复建议" rows={3} />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
