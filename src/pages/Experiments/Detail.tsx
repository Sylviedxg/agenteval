import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Breadcrumb, Card, Tag, Spin, Descriptions, Button, Table, message } from 'antd';
import { PlusOutlined, EyeOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getExperiment } from '../../api/experiments';
import { getTraces, injectMockTrace } from '../../api/traces';
import type { ExperimentStatus } from '../../types/experiment';
import type { Trace } from '../../types/trace';

const statusConfig: Record<ExperimentStatus, { color: string; text: string }> = {
  pending: { color: 'default', text: '待执行' },
  running: { color: 'processing', text: '运行中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
};

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: experiment, isLoading } = useQuery({
    queryKey: ['experiment', id],
    queryFn: () => getExperiment(id!),
    enabled: !!id,
  });

  const { data: traces, isLoading: tracesLoading } = useQuery({
    queryKey: ['traces', id],
    queryFn: () => getTraces(id!),
    enabled: !!id,
  });

  const injectMutation = useMutation({
    mutationFn: injectMockTrace,
    onSuccess: () => {
      message.success('Mock Trace 注入成功');
      queryClient.invalidateQueries({ queryKey: ['traces', id] });
    },
    onError: () => {
      message.error('Mock Trace 注入失败');
    },
  });

  const handleViewTrace = (trace: Trace) => {
    navigate(`/experiments/${id}/traces/${trace.id}`);
  };

  const traceColumns: ColumnsType<Trace> = [
    {
      title: 'Trace ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => id.slice(0, 8) + '...',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'completed' ? 'green' : status === 'failed' ? 'red' : 'blue'}>
          {status}
        </Tag>
      ),
    },
    {
      title: 'Tokens',
      dataIndex: 'total_tokens',
      key: 'total_tokens',
      render: (tokens: number | null) => tokens ?? '—',
    },
    {
      title: '耗时',
      dataIndex: 'total_latency_ms',
      key: 'total_latency_ms',
      render: (ms: number | null) => ms ? `${ms}ms` : '—',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button type="text" icon={<EyeOutlined />} onClick={() => handleViewTrace(record)}>
          查看
        </Button>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  if (!experiment) {
    return <div className="text-white">实验不存在</div>;
  }

  return (
    <div>
      <Breadcrumb
        className="mb-4"
        items={[
          { title: <a onClick={() => navigate('/experiments')}>实验</a> },
          { title: experiment.name },
        ]}
      />

      <Card className="mb-4">
        <div className="flex justify-between items-start">
          <Descriptions title="实验信息" column={2}>
            <Descriptions.Item label="实验名称">{experiment.name}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusConfig[experiment.status]?.color || 'default'}>
                {statusConfig[experiment.status]?.text || experiment.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="总 Case 数">{experiment.total_cases}</Descriptions.Item>
            <Descriptions.Item label="完成数">{experiment.completed_cases}</Descriptions.Item>
            <Descriptions.Item label="综合评分">
              {experiment.overall_score !== null ? experiment.overall_score.toFixed(2) : '—'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(experiment.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => injectMutation.mutate()}
            loading={injectMutation.isPending}
          >
            注入 Mock Trace
          </Button>
        </div>
      </Card>

      <Card title="Trace 列表">
        <Table
          columns={traceColumns}
          dataSource={traces}
          rowKey="id"
          loading={tracesLoading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无 Trace 数据，点击上方按钮注入测试数据' }}
        />
      </Card>

    </div>
  );
}
