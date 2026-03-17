import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Input, Button, Table, Tag, Progress, Descriptions, Space, message, Tabs, Statistic, Row, Col, List } from 'antd';
import { 
  PlayCircleOutlined, 
  CheckCircleOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

interface NodeScore {
  node_name: string;
  agent_name: string;
  eval_layer: string;
  obj_score: number;
  subj_score: number;
  final_score: number;
  is_gate: boolean;
  raw_metrics: Record<string, unknown>;
}

interface LayerScore {
  score: number;
  nodes: number;
}

interface EvaluationResult {
  langfuse_trace_id: string;
  trace_info: {
    id: string;
    name: string;
    session_id: string;
    user_id: string;
    metadata: Record<string, unknown>;
    timestamp: string;
    latency_ms: number;
    total_cost: number;
    total_tokens: number;
  };
  observations_count: number;
  node_scores: Record<string, NodeScore>;
  layer_scores: {
    Layer0: LayerScore;
    Layer1: LayerScore;
    Layer2: LayerScore;
  };
  gates_passed: Record<string, boolean>;
  total_score: number;
  quality_level: string;
  summary: Record<string, unknown>;
}

interface HistoryItem {
  id: string;
  langfuse_trace_id: string;
  trace_name: string;
  session_id: string;
  total_score: number;
  quality_level: string;
  layer0_score: number;
  layer1_score: number;
  layer2_score: number;
  observations_count: number;
  trace_latency_ms: number;
  trace_cost: number;
  all_gates_passed: boolean;
  created_at: string;
}

const EvaluationPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [traceId, setTraceId] = useState('');
  const [secretKey, setSecretKey] = useState('sk-lf-fa7a8d18-b5b0-48cd-8a52-8d8f8596457f');
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await fetch('/api/v1/evaluation/results?limit=20');
      if (response.ok) {
        const data = await response.json();
        setHistory(data.results || []);
      }
    } catch {
      console.error('Failed to fetch history');
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadHistoryResult = async (resultId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/evaluation/results/${resultId}`);
      if (response.ok) {
        const data = await response.json();
        // 转换为 EvaluationResult 格式
        setResult({
          langfuse_trace_id: data.langfuse_trace_id,
          trace_info: {
            id: data.langfuse_trace_id,
            name: data.trace_name,
            session_id: data.session_id,
            user_id: data.user_id,
            metadata: data.trace_metadata || {},
            timestamp: data.trace_timestamp,
            latency_ms: data.trace_latency_ms,
            total_cost: data.trace_cost,
            total_tokens: 0
          },
          observations_count: data.observations_count,
          node_scores: data.node_scores,
          layer_scores: data.layer_scores,
          gates_passed: data.gates_passed,
          total_score: data.total_score,
          quality_level: data.quality_level,
          summary: data.raw_summary || {}
        });
        setTraceId(data.langfuse_trace_id);
        message.success('已加载历史评测结果');
      } else {
        message.error('加载失败');
      }
    } catch {
      message.error('网络错误');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleEvaluate = async () => {
    if (!traceId || !secretKey) {
      message.error('请输入 Trace ID 和 Secret Key');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/evaluation/evaluate-langfuse-trace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          langfuse_trace_id: traceId,
          langfuse_config: {
            host: 'http://172.21.30.114:3208',
            public_key: 'pk-lf-63c63e3a-c38a-45f7-b173-13586793e22e',
            secret_key: secretKey
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        message.success('评测完成，结果已保存');
        fetchHistory(); // 刷新历史记录
      } else {
        const error = await response.json();
        message.error(error.detail || '评测失败');
      }
    } catch {
      message.error('网络错误');
    } finally {
      setLoading(false);
    }
  };

  const getQualityColor = (level: string) => {
    switch (level) {
      case 'A': return '#52c41a';
      case 'B': return '#1890ff';
      case 'C': return '#faad14';
      case 'D': return '#fa8c16';
      case 'F': return '#f5222d';
      default: return '#666';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return '#52c41a';
    if (score >= 0.8) return '#1890ff';
    if (score >= 0.7) return '#faad14';
    if (score >= 0.6) return '#fa8c16';
    return '#f5222d';
  };

  const nodeColumns: ColumnsType<NodeScore & { code: string }> = [
    {
      title: '节点',
      key: 'node',
      width: 250,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Space>
            <span style={{ fontWeight: 500 }}>{record.node_name}</span>
            {record.is_gate && <Tag color="purple">Gate</Tag>}
          </Space>
          <span style={{ fontSize: 12, color: '#999' }}>{record.agent_name}</span>
        </Space>
      ),
    },
    {
      title: '层级',
      dataIndex: 'eval_layer',
      width: 120,
      render: (layer) => {
        let color = 'default';
        if (layer.includes('L0')) color = 'blue';
        else if (layer.includes('L1')) color = 'green';
        else if (layer.includes('L2')) color = 'orange';
        return <Tag color={color}>{layer}</Tag>;
      },
    },
    {
      title: '客观得分',
      dataIndex: 'obj_score',
      width: 120,
      render: (score) => (
        <Progress 
          percent={Math.round(score * 100)} 
          size="small" 
          strokeColor={getScoreColor(score)}
          format={(p) => `${p}%`}
        />
      ),
    },
    {
      title: '主观得分',
      dataIndex: 'subj_score',
      width: 120,
      render: (score) => (
        <Progress 
          percent={Math.round(score * 100)} 
          size="small" 
          strokeColor={getScoreColor(score)}
          format={(p) => `${p}%`}
        />
      ),
    },
    {
      title: '最终得分',
      dataIndex: 'final_score',
      width: 120,
      render: (score) => (
        <span style={{ 
          fontWeight: 600, 
          fontSize: 16, 
          color: getScoreColor(score) 
        }}>
          {(score * 100).toFixed(1)}%
        </span>
      ),
      sorter: (a, b) => a.final_score - b.final_score,
      defaultSortOrder: 'descend',
    },
    {
      title: '原始指标',
      dataIndex: 'raw_metrics',
      width: 200,
      render: (metrics) => {
        if (!metrics || Object.keys(metrics).length === 0) {
          return <span style={{ color: '#999' }}>-</span>;
        }
        return (
          <Space direction="vertical" size={0} style={{ fontSize: 11 }}>
            {Object.entries(metrics).slice(0, 3).map(([key, value]) => (
              <span key={key}>
                {key}: {typeof value === 'number' ? value.toFixed(2) : String(value)}
              </span>
            ))}
          </Space>
        );
      },
    },
  ];

  const renderSummary = () => {
    if (!result) return null;

    return (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="总分"
              value={result.total_score * 100}
              precision={1}
              suffix="%"
              valueStyle={{ color: getScoreColor(result.total_score) }}
            />
            <div style={{ marginTop: 8 }}>
              <Tag 
                color={getQualityColor(result.quality_level)} 
                style={{ fontSize: 18, padding: '4px 16px' }}
              >
                {result.quality_level}级
              </Tag>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ borderTop: '3px solid #1890ff' }}>
            <Statistic
              title="Layer0 (MainAgent)"
              value={result.layer_scores.Layer0.score * 100}
              precision={1}
              suffix="%"
              prefix={<LineChartOutlined />}
            />
            <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
              {result.layer_scores.Layer0.nodes} 节点 · 权重30%
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ borderTop: '3px solid #52c41a' }}>
            <Statistic
              title="Layer1 (单体层)"
              value={result.layer_scores.Layer1.score * 100}
              precision={1}
              suffix="%"
              prefix={<LineChartOutlined />}
            />
            <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
              {result.layer_scores.Layer1.nodes} 节点 · 权重30%
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" style={{ borderTop: '3px solid #faad14' }}>
            <Statistic
              title="Layer2 (协作层)"
              value={result.layer_scores.Layer2.score * 100}
              precision={1}
              suffix="%"
              prefix={<LineChartOutlined />}
            />
            <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
              {result.layer_scores.Layer2.nodes} 节点 · 权重40%
            </div>
          </Card>
        </Col>
      </Row>
    );
  };

  const renderTraceInfo = () => {
    if (!result) return null;

    return (
      <Card title="Trace 信息" size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={4} size="small">
          <Descriptions.Item label="Trace ID">{result.trace_info.id}</Descriptions.Item>
          <Descriptions.Item label="名称">{result.trace_info.name}</Descriptions.Item>
          <Descriptions.Item label="Session">{result.trace_info.session_id}</Descriptions.Item>
          <Descriptions.Item label="用户">{result.trace_info.user_id}</Descriptions.Item>
          <Descriptions.Item label="耗时">{(result.trace_info.latency_ms / 1000).toFixed(1)}s</Descriptions.Item>
          <Descriptions.Item label="成本">${result.trace_info.total_cost.toFixed(4)}</Descriptions.Item>
          <Descriptions.Item label="Observations">{result.observations_count}</Descriptions.Item>
          <Descriptions.Item label="时间">{new Date(result.trace_info.timestamp).toLocaleString()}</Descriptions.Item>
        </Descriptions>
      </Card>
    );
  };

  const renderGates = () => {
    if (!result) return null;

    return (
      <Card title="Gate 检查" size="small" style={{ marginBottom: 16 }}>
        <Space size={16}>
          {Object.entries(result.gates_passed).map(([gate, passed]) => (
            <Tag 
              key={gate} 
              icon={passed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              color={passed ? 'success' : 'error'}
              style={{ padding: '4px 12px', fontSize: 14 }}
            >
              {gate}
            </Tag>
          ))}
        </Space>
      </Card>
    );
  };

  const getNodeScoresArray = () => {
    if (!result) return [];
    return Object.entries(result.node_scores).map(([code, score]) => ({
      code,
      ...score
    }));
  };

  const tabItems = [
    {
      key: 'all',
      label: `全部节点 (${getNodeScoresArray().length})`,
      children: (
        <Table
          columns={nodeColumns}
          dataSource={getNodeScoresArray()}
          rowKey="code"
          size="small"
          pagination={{ pageSize: 15 }}
        />
      ),
    },
    {
      key: 'l0',
      label: `L0 MainAgent`,
      children: (
        <Table
          columns={nodeColumns}
          dataSource={getNodeScoresArray().filter(n => n.eval_layer.includes('L0'))}
          rowKey="code"
          size="small"
          pagination={false}
        />
      ),
    },
    {
      key: 'l1',
      label: `L1 单体层`,
      children: (
        <Table
          columns={nodeColumns}
          dataSource={getNodeScoresArray().filter(n => n.eval_layer.includes('L1'))}
          rowKey="code"
          size="small"
          pagination={{ pageSize: 10 }}
        />
      ),
    },
    {
      key: 'l2',
      label: `L2 协作层`,
      children: (
        <Table
          columns={nodeColumns}
          dataSource={getNodeScoresArray().filter(n => n.eval_layer.includes('L2'))}
          rowKey="code"
          size="small"
          pagination={false}
        />
      ),
    },
    {
      key: 'gates',
      label: (
        <span>
          <ThunderboltOutlined />
          Gate节点
        </span>
      ),
      children: (
        <Table
          columns={nodeColumns}
          dataSource={getNodeScoresArray().filter(n => n.is_gate)}
          rowKey="code"
          size="small"
          pagination={false}
        />
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <PlayCircleOutlined />
            <span>Langfuse Trace 评测</span>
          </Space>
        }
      >
        <div style={{ marginBottom: 24 }}>
          <Space size={16}>
            <Input
              placeholder="Langfuse Trace ID"
              value={traceId}
              onChange={(e) => setTraceId(e.target.value)}
              style={{ width: 350 }}
            />
            <Input.Password
              placeholder="Langfuse Secret Key (sk-lf-...)"
              value={secretKey}
              onChange={(e) => setSecretKey(e.target.value)}
              style={{ width: 350 }}
            />
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />}
              onClick={handleEvaluate}
              loading={loading}
            >
              开始评测
            </Button>
          </Space>
        </div>

        {result && (
          <>
            {renderSummary()}
            {renderTraceInfo()}
            {renderGates()}
            
            <Card title="节点评分详情" size="small">
              <Tabs items={tabItems} />
            </Card>
          </>
        )}
      </Card>

      {/* 评测历史记录 */}
      <Card 
        title="评测历史记录" 
        style={{ marginTop: 16 }}
        loading={historyLoading}
      >
        <List
          dataSource={history}
          renderItem={(item) => (
            <List.Item
              style={{ cursor: 'pointer' }}
              onClick={() => loadHistoryResult(item.id)}
              actions={[
                <Tag color={getQualityColor(item.quality_level)} key="level">
                  {item.quality_level}级
                </Tag>,
                <span key="score" style={{ fontWeight: 600, color: getScoreColor(item.total_score) }}>
                  {(item.total_score * 100).toFixed(1)}%
                </span>,
                <Button type="link" size="small" key="view">查看详情</Button>,
                <Button 
                  type="link" 
                  size="small" 
                  key="tree"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/traces/${item.langfuse_trace_id}`);
                  }}
                >
                  Trace树
                </Button>
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <span>{item.trace_name || 'Unknown'}</span>
                    <Tag>{item.langfuse_trace_id.slice(0, 8)}...</Tag>
                    {item.all_gates_passed ? (
                      <Tag color="success" icon={<CheckCircleOutlined />}>Gates通过</Tag>
                    ) : (
                      <Tag color="error" icon={<CloseCircleOutlined />}>Gates失败</Tag>
                    )}
                  </Space>
                }
                description={
                  <Space size={16} style={{ fontSize: 12, color: '#999' }}>
                    <span>Session: {item.session_id}</span>
                    <span>L0: {(item.layer0_score * 100).toFixed(0)}%</span>
                    <span>L1: {(item.layer1_score * 100).toFixed(0)}%</span>
                    <span>L2: {(item.layer2_score * 100).toFixed(0)}%</span>
                    <span>Obs: {item.observations_count}</span>
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                  </Space>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无评测记录' }}
        />
      </Card>
    </div>
  );
};

export default EvaluationPage;
