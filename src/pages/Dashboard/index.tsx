import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, Statistic, Table, Tag, Spin } from 'antd';
import {
  ExperimentOutlined,
  BugOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getDashboardStats, type RecentExperiment } from '../../api/dashboard';

const statusConfig: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '待执行' },
  running: { color: 'processing', text: '运行中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
};

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: getDashboardStats,
  });

  const columns: ColumnsType<RecentExperiment> = [
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
      render: (status: string) => (
        <Tag color={statusConfig[status]?.color || 'default'}>
          {statusConfig[status]?.text || status}
        </Tag>
      ),
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
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
  ];

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-white text-xl font-semibold mb-6">总览</h1>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card className="bg-[#1e293b]">
          <Statistic
            title={<span className="text-gray-400">总实验数</span>}
            value={stats?.total_experiments || 0}
            prefix={<ExperimentOutlined className="text-blue-400" />}
            styles={{ content: { color: '#60a5fa' } }}
          />
        </Card>
        <Card className="bg-[#1e293b]">
          <Statistic
            title={<span className="text-gray-400">总 BadCase 数</span>}
            value={stats?.total_badcases || 0}
            prefix={<BugOutlined className="text-red-400" />}
            styles={{ content: { color: '#f87171' } }}
          />
        </Card>
        <Card className="bg-[#1e293b]">
          <Statistic
            title={<span className="text-gray-400">待处理 BadCase</span>}
            value={stats?.open_badcases || 0}
            prefix={<WarningOutlined className="text-orange-400" />}
            styles={{ content: { color: '#fb923c' } }}
          />
        </Card>
        <Card className="bg-[#1e293b]">
          <Statistic
            title={<span className="text-gray-400">已解决 BadCase</span>}
            value={stats?.resolved_badcases || 0}
            prefix={<CheckCircleOutlined className="text-green-400" />}
            styles={{ content: { color: '#4ade80' } }}
          />
        </Card>
      </div>

      <Card className="bg-[#1e293b]" title={<span className="text-white">最近实验</span>}>
        <Table
          columns={columns}
          dataSource={stats?.recent_experiments || []}
          rowKey="id"
          pagination={false}
          locale={{ emptyText: '暂无实验数据' }}
        />
      </Card>
    </div>
  );
}
