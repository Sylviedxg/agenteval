import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Tabs, Descriptions, Badge, Space, Button, Tooltip, message } from 'antd';
import { 
  NodeIndexOutlined, 
  ThunderboltOutlined,
  ReloadOutlined,
  EyeOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

interface EvalNodeDefinition {
  id: string;
  agent_name: string;
  node_name: string;
  node_code: string;
  layer_tag: string;
  eval_layer: string;
  obj_metric_1_name: string | null;
  obj_metric_1_source: string | null;
  obj_metric_2_name: string | null;
  obj_metric_2_source: string | null;
  obj_metric_3_name: string | null;
  obj_metric_3_source: string | null;
  subj_metric_1_name: string | null;
  subj_metric_1_method: string | null;
  subj_metric_2_name: string | null;
  subj_metric_2_method: string | null;
  obj_score_formula: string | null;
  subj_score_formula: string | null;
  final_score_formula: string;
  belongs_to: string;
  layer_weight: string;
  node_weight_rule: string;
  is_gate: boolean;
  gate_type: string | null;
  gate_condition: string | null;
  remark: string | null;
  sort_order: number;
  is_active: boolean;
}

interface GateDefinition {
  id: string;
  gate_type: string;
  name: string;
  description: string | null;
  trigger_point: string;
  source_layer: string | null;
  target_layer: string | null;
  pass_conditions: Record<string, string | number | boolean>;
  on_fail_action: string;
  retry_limit: number;
  related_node_codes: string[] | null;
  sort_order: number;
  is_active: boolean;
}

interface EvalNodeOverview {
  total_nodes: number;
  l0_nodes: EvalNodeDefinition[];
  l1_nodes: EvalNodeDefinition[];
  l2_nodes: EvalNodeDefinition[];
  l3_nodes: EvalNodeDefinition[];
  gates: GateDefinition[];
}

const EvalNodesPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState<EvalNodeOverview | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/eval-nodes/overview');
      if (response.ok) {
        const data = await response.json();
        setOverview(data);
      } else {
        message.error('获取评测节点数据失败');
      }
    } catch {
      message.error('网络错误');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const getLayerColor = (layer: string) => {
    if (layer.includes('L0') || layer.includes('MainAgent')) return 'blue';
    if (layer.includes('L1') || layer.includes('单体')) return 'green';
    if (layer.includes('L2') || layer.includes('协作')) return 'orange';
    if (layer.includes('L3') || layer.includes('系统')) return 'red';
    return 'default';
  };

  const getGateColor = (gateType: string) => {
    switch (gateType) {
      case 'Gate0': return '#1890ff';
      case 'GateA': return '#52c41a';
      case 'GateB': return '#faad14';
      case 'GateC': return '#f5222d';
      default: return '#666';
    }
  };

  const nodeColumns: ColumnsType<EvalNodeDefinition> = [
    {
      title: '节点',
      key: 'node',
      width: 280,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Space>
            <span style={{ fontWeight: 500 }}>{record.node_name}</span>
            {record.is_gate && (
              <Tag color={getGateColor(record.gate_type || '')} style={{ marginLeft: 4 }}>
                {record.gate_type}
              </Tag>
            )}
          </Space>
          <span style={{ fontSize: 12, color: '#999' }}>{record.agent_name}</span>
        </Space>
      ),
    },
    {
      title: '层级',
      dataIndex: 'eval_layer',
      width: 120,
      render: (layer) => <Tag color={getLayerColor(layer)}>{layer}</Tag>,
    },
    {
      title: '客观指标',
      key: 'obj_metrics',
      width: 200,
      render: (_, record) => (
        <Space direction="vertical" size={0} style={{ fontSize: 12 }}>
          {record.obj_metric_1_name && (
            <Tooltip title={record.obj_metric_1_source}>
              <span>• {record.obj_metric_1_name}</span>
            </Tooltip>
          )}
          {record.obj_metric_2_name && (
            <Tooltip title={record.obj_metric_2_source}>
              <span>• {record.obj_metric_2_name}</span>
            </Tooltip>
          )}
          {record.obj_metric_3_name && (
            <Tooltip title={record.obj_metric_3_source}>
              <span>• {record.obj_metric_3_name}</span>
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: '主观指标',
      key: 'subj_metrics',
      width: 180,
      render: (_, record) => (
        <Space direction="vertical" size={0} style={{ fontSize: 12 }}>
          {record.subj_metric_1_name && (
            <Tooltip title={record.subj_metric_1_method}>
              <span>• {record.subj_metric_1_name}</span>
            </Tooltip>
          )}
          {record.subj_metric_2_name && (
            <Tooltip title={record.subj_metric_2_method}>
              <span>• {record.subj_metric_2_name}</span>
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: '评分公式',
      dataIndex: 'final_score_formula',
      width: 150,
      render: (formula) => <code style={{ fontSize: 11 }}>{formula}</code>,
    },
    {
      title: '权重规则',
      dataIndex: 'node_weight_rule',
      width: 180,
      ellipsis: true,
    },
  ];

  const gateColumns: ColumnsType<GateDefinition> = [
    {
      title: 'Gate',
      dataIndex: 'gate_type',
      width: 100,
      render: (type) => (
        <Tag color={getGateColor(type)} style={{ fontWeight: 600 }}>{type}</Tag>
      ),
    },
    {
      title: '名称',
      dataIndex: 'name',
      width: 180,
    },
    {
      title: '触发点',
      dataIndex: 'trigger_point',
      width: 200,
    },
    {
      title: '层级流转',
      key: 'layers',
      width: 150,
      render: (_, record) => (
        <Space>
          {record.source_layer && <Tag>{record.source_layer}</Tag>}
          {record.source_layer && record.target_layer && <span>→</span>}
          {record.target_layer && <Tag>{record.target_layer}</Tag>}
        </Space>
      ),
    },
    {
      title: '通过条件',
      dataIndex: 'pass_conditions',
      width: 250,
      render: (conditions) => (
        <Space direction="vertical" size={0} style={{ fontSize: 12 }}>
          {Object.entries(conditions || {}).map(([key, value]) => (
            <span key={key}>• {key}: {String(value)}</span>
          ))}
        </Space>
      ),
    },
    {
      title: '失败处理',
      key: 'fail_action',
      width: 150,
      render: (_, record) => (
        <Space>
          <Tag color={record.on_fail_action === 'manual_review' ? 'red' : 'orange'}>
            {record.on_fail_action}
          </Tag>
          <span style={{ fontSize: 12, color: '#999' }}>重试{record.retry_limit}次</span>
        </Space>
      ),
    },
  ];

  const renderOverviewCards = () => {
    if (!overview) return null;

    const layers = [
      { key: 'l0', title: 'L0 MainAgent', nodes: overview.l0_nodes, color: '#1890ff', weight: '30%' },
      { key: 'l1', title: 'L1 单体层', nodes: overview.l1_nodes, color: '#52c41a', weight: '30%' },
      { key: 'l2', title: 'L2 协作层', nodes: overview.l2_nodes, color: '#faad14', weight: '40%' },
      { key: 'l3', title: 'L3 系统层', nodes: overview.l3_nodes, color: '#f5222d', weight: '-' },
    ];

    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {layers.map((layer) => (
          <Card key={layer.key} size="small" style={{ borderTop: `3px solid ${layer.color}` }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 28, fontWeight: 600, color: layer.color }}>
                {layer.nodes.length}
              </div>
              <div style={{ fontSize: 14, color: '#666' }}>{layer.title}</div>
              <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                权重: {layer.weight}
              </div>
              <div style={{ marginTop: 8 }}>
                {layer.nodes.filter(n => n.is_gate).length > 0 && (
                  <Tag color="purple" style={{ fontSize: 11 }}>
                    {layer.nodes.filter(n => n.is_gate).length} Gate节点
                  </Tag>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  };

  const renderLayerNodes = (nodes: EvalNodeDefinition[]) => {
    const gateNodes = nodes.filter(n => n.is_gate);
    const normalNodes = nodes.filter(n => !n.is_gate);

    return (
      <div>
        {gateNodes.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>
              <ThunderboltOutlined style={{ marginRight: 8, color: '#faad14' }} />
              Gate节点 ({gateNodes.length})
            </div>
            <Table
              columns={nodeColumns}
              dataSource={gateNodes}
              rowKey="id"
              size="small"
              pagination={false}
              style={{ marginBottom: 16 }}
            />
          </div>
        )}
        <div>
          <div style={{ marginBottom: 8, fontWeight: 500 }}>
            <NodeIndexOutlined style={{ marginRight: 8 }} />
            普通节点 ({normalNodes.length})
          </div>
          <Table
            columns={nodeColumns}
            dataSource={normalNodes}
            rowKey="id"
            size="small"
            pagination={false}
          />
        </div>
      </div>
    );
  };

  const tabItems = [
    {
      key: 'overview',
      label: (
        <span>
          <EyeOutlined />
          概览
        </span>
      ),
      children: (
        <div>
          {renderOverviewCards()}
          
          <Card title="Gate质量关口" size="small" style={{ marginBottom: 16 }}>
            <Table
              columns={gateColumns}
              dataSource={overview?.gates || []}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>

          <Card title="评分聚合规则" size="small">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="节点得分">
                <code>客观指标×0.7 + 主观指标×0.3</code>
              </Descriptions.Item>
              <Descriptions.Item label="层级聚合">
                <code>各节点加权平均（Gate节点×1.5~2.0）</code>
              </Descriptions.Item>
              <Descriptions.Item label="Investigation总分">
                <code>Layer0×0.3 + Layer1×0.3 + Layer2×0.4</code>
              </Descriptions.Item>
              <Descriptions.Item label="主观评估流程">
                LLM初评 → 低分人工复核 → 反哺prompt
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </div>
      ),
    },
    {
      key: 'l0',
      label: (
        <span>
          <Badge color="#1890ff" />
          L0 MainAgent ({overview?.l0_nodes.length || 0})
        </span>
      ),
      children: overview ? renderLayerNodes(overview.l0_nodes) : null,
    },
    {
      key: 'l1',
      label: (
        <span>
          <Badge color="#52c41a" />
          L1 单体层 ({overview?.l1_nodes.length || 0})
        </span>
      ),
      children: overview ? renderLayerNodes(overview.l1_nodes) : null,
    },
    {
      key: 'l2',
      label: (
        <span>
          <Badge color="#faad14" />
          L2 协作层 ({overview?.l2_nodes.length || 0})
        </span>
      ),
      children: overview ? renderLayerNodes(overview.l2_nodes) : null,
    },
    {
      key: 'l3',
      label: (
        <span>
          <Badge color="#f5222d" />
          L3 系统层 ({overview?.l3_nodes.length || 0})
        </span>
      ),
      children: overview ? renderLayerNodes(overview.l3_nodes) : null,
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <NodeIndexOutlined />
            <span>评测节点体系</span>
            <Tag color="blue">{overview?.total_nodes || 0} 节点</Tag>
            <Tag color="purple">{overview?.gates.length || 0} Gate</Tag>
          </Space>
        }
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchOverview} loading={loading}>
            刷新
          </Button>
        }
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>
    </div>
  );
};

export default EvalNodesPage;
