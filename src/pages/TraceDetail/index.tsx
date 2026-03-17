import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Spin, Row, Col, Statistic, Tag, message } from 'antd';
import {
  ClockCircleOutlined,
  DollarOutlined,
  NodeIndexOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import TraceTree, { type TraceNode } from '../../components/TraceTree';
import NodeDetail from '../../components/NodeDetail';
import styles from './index.module.css';

interface TraceInfo {
  id: string;
  name: string;
  session_id: string;
  user_id: string;
  timestamp: string;
  latency_ms: number;
  total_cost: number;
  observations_count: number;
}

interface EvaluationData {
  trace_info: TraceInfo;
  trace_tree: TraceNode[];
  node_scores: Record<string, {
    node_name: string;
    obj_score: number;
    subj_score: number;
    final_score: number;
  }>;
  total_score: number;
  quality_level: string;
  gates_passed: Record<string, boolean>;
}

const TraceDetail: React.FC = () => {
  const { traceId } = useParams<{ traceId: string }>();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<EvaluationData | null>(null);
  const [selectedNode, setSelectedNode] = useState<TraceNode | null>(null);

  const fetchTraceData = useCallback(async (id: string) => {
    setLoading(true);
    try {
      // 获取trace树数据
      const treeResponse = await fetch(`/api/v1/evaluation/trace-tree/${id}`);
      if (!treeResponse.ok) {
        message.error('获取Trace数据失败');
        return;
      }
      const treeResult = await treeResponse.json();
      
      // 尝试获取评测结果（可能不存在）
      let evalData = {
        node_scores: {},
        total_score: 0,
        quality_level: 'C',
        gates_passed: {},
      };
      
      try {
        const evalResponse = await fetch(`/api/v1/evaluation/results?limit=1&trace_id=${id}`);
        if (evalResponse.ok) {
          const evalResult = await evalResponse.json();
          if (evalResult.results && evalResult.results.length > 0) {
            const r = evalResult.results[0];
            evalData = {
              node_scores: r.node_scores || {},
              total_score: r.total_score || 0,
              quality_level: r.quality_level || 'C',
              gates_passed: r.gates_passed || {},
            };
          }
        }
      } catch {
        // 评测结果不存在，使用默认值
      }
      
      // 构建Trace树
      const traceTree = buildTraceTree(treeResult.observations || []);
      
      setData({
        trace_info: {
          ...treeResult.trace_info,
          observations_count: treeResult.observations_count,
        },
        trace_tree: traceTree,
        ...evalData,
      });
    } catch (error) {
      console.error('Fetch error:', error);
      message.error('网络错误');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (traceId) {
      fetchTraceData(traceId);
    }
  }, [traceId, fetchTraceData]);

  // 从observations构建Trace树
  const buildTraceTree = (observations: Array<Record<string, unknown>>): TraceNode[] => {
    if (!observations || observations.length === 0) {
      return [];
    }

    // 按parentObservationId分组
    const childrenMap: Record<string, Array<Record<string, unknown>>> = {};
    const obsMap: Record<string, Record<string, unknown>> = {};
    
    observations.forEach((obs) => {
      const obsId = obs.id as string;
      obsMap[obsId] = obs;
      
      const parentId = obs.parentObservationId as string | null;
      if (parentId) {
        if (!childrenMap[parentId]) {
          childrenMap[parentId] = [];
        }
        childrenMap[parentId].push(obs);
      }
    });

    // 找出根节点：没有parentObservationId，或者parentObservationId不在当前observations中
    const rootNodes: Array<Record<string, unknown>> = [];
    observations.forEach((obs) => {
      const parentId = obs.parentObservationId as string | null;
      if (!parentId || !obsMap[parentId]) {
        rootNodes.push(obs);
      }
    });

    // 递归构建树
    const buildNode = (obs: Record<string, unknown>): TraceNode => {
      const obsId = obs.id as string;
      const obsName = obs.name as string || 'Unknown';
      const obsType = obs.type as string || 'SPAN';
      const children = childrenMap[obsId] || [];

      // 确定节点类型
      let nodeType: TraceNode['type'] = 'SPAN';
      if (obsType === 'GENERATION') {
        nodeType = 'LLM';
      } else if (obsName.includes('Agent') || obsName.includes('agent')) {
        if (obsName.includes('Main') || obsName === 'StrategicAnalysisAgent') {
          nodeType = 'MainAgent';
        } else {
          nodeType = 'SubAgent';
        }
      } else if (obsName.includes('search') || obsName.includes('browse') || obsName.includes('tool')) {
        nodeType = 'Tool';
      } else if (obsName.includes('bubble') || obsName.includes('Bubble')) {
        nodeType = 'Bubble';
      } else if (obsName.includes('Gate') || obsName.includes('gate')) {
        nodeType = 'Gate';
      }

      // 计算耗时
      let durationMs = 0;
      const startTime = obs.startTime as string | undefined;
      const endTime = obs.endTime as string | undefined;
      if (startTime && endTime) {
        durationMs = new Date(endTime).getTime() - new Date(startTime).getTime();
      }

      // 获取tokens
      const usage = obs.usage as Record<string, number> | undefined;
      const tokens = usage?.totalTokens || usage?.total || 0;

      return {
        id: obsId,
        name: obsName,
        type: nodeType,
        duration_ms: durationMs,
        tokens: tokens,
        status: obs.level === 'ERROR' ? 'error' : 'success',
        input: obs.input ? JSON.stringify(obs.input, null, 2) : undefined,
        output: obs.output ? JSON.stringify(obs.output, null, 2) : undefined,
        metadata: obs.metadata as Record<string, unknown> | undefined,
        children: children.map(buildNode),
      };
    };

    return rootNodes.map(buildNode);
  };

  const handleNodeSelect = (node: TraceNode) => {
    setSelectedNode(node);
  };

  const getQualityColor = (level: string): string => {
    switch (level) {
      case 'A': return '#52c41a';
      case 'B': return '#1677ff';
      case 'C': return '#faad14';
      case 'D': return '#ff4d4f';
      default: return '#8c8c8c';
    }
  };

  if (loading) {
    return (
      <div className={styles.loadingWrapper}>
        <Spin size="large" tip="加载Trace数据中..." />
      </div>
    );
  }

  if (!data) {
    return (
      <div className={styles.errorWrapper}>
        <p>无法加载Trace数据</p>
      </div>
    );
  }

  const allGatesPassed = Object.values(data.gates_passed).every(v => v);

  return (
    <div className={styles.container}>
      {/* 顶部统计 */}
      <Card className={styles.statsCard}>
        <Row gutter={24}>
          <Col span={4}>
            <Statistic
              title="总分"
              value={(data.total_score * 100).toFixed(1)}
              suffix="%"
              valueStyle={{ color: getQualityColor(data.quality_level) }}
            />
            <Tag color={getQualityColor(data.quality_level)} style={{ marginTop: 8 }}>
              {data.quality_level}级
            </Tag>
          </Col>
          <Col span={4}>
            <Statistic
              title="Trace名称"
              value={data.trace_info.name}
              valueStyle={{ fontSize: 16 }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="耗时"
              value={(data.trace_info.latency_ms / 1000).toFixed(1)}
              suffix="s"
              prefix={<ClockCircleOutlined />}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="成本"
              value={data.trace_info.total_cost.toFixed(4)}
              prefix={<DollarOutlined />}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="Observations"
              value={data.trace_info.observations_count}
              prefix={<NodeIndexOutlined />}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="Gate检查"
              value={allGatesPassed ? '全部通过' : '存在失败'}
              valueStyle={{ color: allGatesPassed ? '#52c41a' : '#ff4d4f', fontSize: 16 }}
              prefix={allGatesPassed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
            />
          </Col>
        </Row>
      </Card>

      {/* 主体内容：Trace树 + 节点详情 */}
      <Row gutter={16} className={styles.mainContent}>
        <Col span={12}>
          <Card
            title={
              <span>
                Trace树 — <span style={{ color: '#8c8c8c', fontWeight: 400 }}>
                  {data.trace_info.name}
                </span>
              </span>
            }
            className={styles.treeCard}
          >
            <TraceTree
              nodes={data.trace_tree}
              selectedId={selectedNode?.id}
              onSelect={handleNodeSelect}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="节点详情" className={styles.detailCard}>
            <NodeDetail node={selectedNode} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default TraceDetail;
