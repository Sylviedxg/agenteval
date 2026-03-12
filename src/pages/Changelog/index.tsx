import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Timeline, Button, Modal, Form, Input, Select, message, Tag, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { getChangelogs, createChangelog } from '../../api/changelogs';
import { getProducts } from '../../api/products';
import type { ChangelogCreate, ChangeType } from '../../types/changelog';

const changeTypeConfig: Record<ChangeType, { color: string; text: string }> = {
  prompt_update: { color: 'blue', text: 'Prompt 更新' },
  model_change: { color: 'purple', text: '模型更换' },
  tool_update: { color: 'cyan', text: '工具更新' },
  config_change: { color: 'orange', text: '配置变更' },
};

export default function Changelog() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: changelogs, isLoading } = useQuery({
    queryKey: ['changelogs'],
    queryFn: () => getChangelogs(),
  });

  const { data: products } = useQuery({
    queryKey: ['products'],
    queryFn: getProducts,
  });

  const createMutation = useMutation({
    mutationFn: createChangelog,
    onSuccess: () => {
      message.success('变更记录创建成功');
      queryClient.invalidateQueries({ queryKey: ['changelogs'] });
      setIsModalOpen(false);
      form.resetFields();
    },
    onError: () => {
      message.error('变更记录创建失败');
    },
  });

  const handleCreate = (values: ChangelogCreate) => {
    if (!values.product_id && products && products.length > 0) {
      values.product_id = products[0].id;
    }
    createMutation.mutate(values);
  };

  const timelineItems = changelogs?.map((log) => ({
    key: log.id,
    color: changeTypeConfig[log.change_type]?.color || 'gray',
    label: (
      <div className="text-gray-400 text-sm">
        {new Date(log.created_at).toLocaleString('zh-CN')}
      </div>
    ),
    children: (
      <div className="pb-4">
        <div className="flex items-center gap-2 mb-1">
          <Tag color={changeTypeConfig[log.change_type]?.color || 'default'}>
            {changeTypeConfig[log.change_type]?.text || log.change_type}
          </Tag>
          <span className="text-white font-medium">{log.title}</span>
        </div>
        {log.description && (
          <div className="text-gray-300 text-sm">{log.description}</div>
        )}
      </div>
    ),
  }));

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-white text-xl font-semibold">变更记录</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          记录变更
        </Button>
      </div>

      {isLoading ? (
        <div className="text-gray-400">加载中...</div>
      ) : changelogs && changelogs.length > 0 ? (
        <Timeline items={timelineItems} />
      ) : (
        <div className="text-gray-400 text-center py-8">暂无变更记录</div>
      )}

      <Modal
        title="记录变更"
        open={isModalOpen}
        onCancel={() => { setIsModalOpen(false); form.resetFields(); }}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="change_type"
            label="变更类型"
            rules={[{ required: true, message: '请选择变更类型' }]}
          >
            <Select placeholder="请选择变更类型">
              <Select.Option value="prompt_update">Prompt 更新</Select.Option>
              <Select.Option value="model_change">模型更换</Select.Option>
              <Select.Option value="tool_update">工具更新</Select.Option>
              <Select.Option value="config_change">配置变更</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="请输入变更标题" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入变更描述" rows={3} />
          </Form.Item>
          <Form.Item name="impact_assessment" label="影响评估">
            <Input.TextArea placeholder="请输入影响评估" rows={2} />
          </Form.Item>
          <Form.Item className="mb-0 flex justify-end">
            <Space>
              <Button onClick={() => { setIsModalOpen(false); form.resetFields(); }}>取消</Button>
              <Button type="primary" htmlType="submit" loading={createMutation.isPending}>创建</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
