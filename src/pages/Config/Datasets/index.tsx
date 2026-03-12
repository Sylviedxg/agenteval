import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, Button, Modal, Form, Input, message, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getDatasets, createDataset } from '../../../api/experiments';
import type { Dataset, DatasetCreate } from '../../../types/experiment';

export default function Datasets() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: getDatasets,
  });

  const createMutation = useMutation({
    mutationFn: createDataset,
    onSuccess: () => {
      message.success('评测集创建成功');
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      setIsModalOpen(false);
      form.resetFields();
    },
    onError: () => {
      message.error('评测集创建失败');
    },
  });

  const handleCreate = (values: DatasetCreate) => {
    createMutation.mutate(values);
  };

  const columns: ColumnsType<Dataset> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: 'Case 数',
      dataIndex: 'case_count',
      key: 'case_count',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-white text-xl font-semibold">评测集</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          新建评测集
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={datasets}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="新建评测集"
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="name"
            label="评测集名称"
            rules={[{ required: true, message: '请输入评测集名称' }]}
          >
            <Input placeholder="请输入评测集名称" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入描述" rows={3} />
          </Form.Item>

          <Form.Item name="version" label="版本" initialValue="1.0.0">
            <Input placeholder="请输入版本号" />
          </Form.Item>

          <Form.Item className="mb-0 flex justify-end">
            <Space>
              <Button onClick={() => { setIsModalOpen(false); form.resetFields(); }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
