import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Breadcrumb, Card, Tag, Spin, Tabs, Collapse, Slider, Empty } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  ToolOutlined,
  RobotOutlined,
  ArrowDownOutlined,
  ArrowUpOutlined,
} from '@ant-design/icons';
import { getExperiment } from '../../api/experiments';
import { getTrace } from '../../api/traces';
import type { TraceNode, TraceEvent } from '../../types/trace';

const statusIcons: Record<string, React.ReactNode> = {
  success: <CheckCircleOutlined className="text-green-400" />,
  failed: <CloseCircleOutlined className="text-red-400" />,
  running: <LoadingOutlined className="text-blue-400" spin />,
  pending: <ClockCircleOutlined className="text-gray-400" />,
};

const eventTypeConfig: Record<string, { icon: React.ReactNode; color: string }> = {
  tool_call: { icon: <ToolOutlined />, color: 'cyan' },
  llm_call: { icon: <RobotOutlined />, color: 'purple' },
  delegate: { icon: <ArrowDownOutlined />, color: 'blue' },
  bubble: { icon: <ArrowUpOutlined />, color: 'green' },
};

function EventItem({ event }: { event: TraceEvent }) {
  const config = eventTypeConfig[event.event_type] || { icon: null, color: 'default' };

  const getEventTitle = () => {
    switch (event.event_type) {
      case 'tool_call':
        return `${event.tool_name} · ${event.latency_ms}ms`;
      case 'llm_call':
        return `${event.model} · ${(event.prompt_tokens || 0) + (event.completion_tokens || 0)} tokens`;
      case 'delegate':
        return `下发给 ${event.card_type}`;
      case 'bubble':
        return event.finding_type || 'Bubble';
      default:
        return event.event_type;
    }
  };

  const getEventContent = () => {
    switch (event.event_type) {
      case 'tool_call':
        return (
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-400">Input: </span>
              <pre className="bg-[#0f172a] p-2 rounded mt-1 overflow-auto text-xs">
                {JSON.stringify(event.tool_input, null, 2)}
              </pre>
            </div>
            <div>
              <span className="text-gray-400">Output: </span>
              <pre className="bg-[#0f172a] p-2 rounded mt-1 overflow-auto text-xs">
                {JSON.stringify(event.tool_output, null, 2)}
              </pre>
            </div>
          </div>
        );
      case 'llm_call':
        return (
          <div className="space-y-2 text-sm">
            <div><span className="text-gray-400">Input: </span>{event.input_summary}</div>
            <div><span className="text-gray-400">Output: </span>{event.output_summary}</div>
          </div>
        );
      case 'delegate':
        return (
          <div className="text-sm">
            <span className="text-gray-400">Instruction: </span>
            {event.instruction?.slice(0, 100)}{(event.instruction?.length || 0) > 100 ? '...' : ''}
          </div>
        );
      case 'bubble':
        return (
          <div className="text-sm">
            <Tag color="green">{event.finding_type}</Tag>
            <div className="mt-1">{event.content?.slice(0, 150)}{(event.content?.length || 0) > 150 ? '...' : ''}</div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <Collapse
      size="small"
      items={[{
        key: '1',
        label: (
          <div className="flex items-center gap-2">
            <span className={`text-${config.color}-400`}>{config.icon}</span>
            <span>{getEventTitle()}</span>
          </div>
        ),
        children: getEventContent(),
      }]}
    />
  );
}

function NodeDetailPanel({ node }: { node: TraceNode }) {
  const tabItems = [
    {
      key: 'events',
      label: '事件流',
      children: (
        <div className="space-y-2 max-h-[400px] overflow-auto">
          {node.events && node.events.length > 0 ? (
            node.events.map((event, idx) => (
              <EventItem key={idx} event={event} />
            ))
          ) : (
            <Empty description="暂无事件" />
          )}
        </div>
      ),
    },
    {
      key: 'io',
      label: '输入/输出',
      children: (
        <div className="space-y-4">
          <div>
            <div className="text-gray-400 text-sm mb-1">输入</div>
            <pre className="bg-[#0f172a] p-3 rounded text-sm overflow-auto whitespace-pre-wrap">
              {node.input_summary || '—'}
            </pre>
          </div>
          <div>
            <div className="text-gray-400 text-sm mb-1">输出</div>
            <pre className="bg-[#0f172a] p-3 rounded text-sm overflow-auto whitespace-pre-wrap">
              {node.output_summary || '—'}
            </pre>
          </div>
        </div>
      ),
    },
    {
      key: 'scores',
      label: '评分',
      children: (
        <div className="space-y-6">
          <div>
            <div className="text-gray-300 font-medium mb-3">客观指标</div>
            {Object.keys(node.auto_scores || {}).length > 0 ? (
              Object.entries(node.auto_scores || {}).map(([name, score]) => (
                <div key={name} className="flex items-center gap-4 mb-2">
                  <span className="text-gray-400 w-40">{name}</span>
                  <div className="flex-1">
                    <div className="bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${(score / 10) * 100}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-white w-10 text-right">{score.toFixed(1)}</span>
                </div>
              ))
            ) : (
              <div className="text-gray-500">暂无客观指标</div>
            )}
          </div>
          <div>
            <div className="text-gray-300 font-medium mb-3">主观指标</div>
            {Object.keys(node.manual_scores || {}).length > 0 ? (
              Object.entries(node.manual_scores || {}).map(([name, score]) => (
                <div key={name} className="mb-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-gray-400">{name}</span>
                    <span className="text-white">{score}</span>
                  </div>
                  <Slider min={0} max={10} step={0.5} value={score} disabled />
                </div>
              ))
            ) : (
              <div className="text-gray-500">暂无主观指标</div>
            )}
          </div>
        </div>
      ),
    },
  ];

  return <Tabs items={tabItems} />;
}

export default function TraceDetail() {
  const { id: experimentId, traceId } = useParams<{ id: string; traceId: string }>();
  const navigate = useNavigate();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const { data: experiment } = useQuery({
    queryKey: ['experiment', experimentId],
    queryFn: () => getExperiment(experimentId!),
    enabled: !!experimentId,
  });

  const { data: trace, isLoading } = useQuery({
    queryKey: ['trace', traceId],
    queryFn: () => getTrace(traceId!),
    enabled: !!traceId,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  if (!trace) {
    return <div className="text-white">Trace 不存在</div>;
  }

  const rawTrace = trace.raw_trace;
  const selectedNode = rawTrace?.nodes.find((n) => n.node_id === selectedNodeId);

  return (
    <div>
      <Breadcrumb
        className="mb-4"
        items={[
          { title: <a onClick={() => navigate('/experiments')}>实验</a> },
          { title: <a onClick={() => navigate(`/experiments/${experimentId}`)}>{experiment?.name || '实验详情'}</a> },
          { title: 'Trace 详情' },
        ]}
      />

      <Card className="mb-4">
        <div className="flex items-center gap-6">
          <div>
            <span className="text-gray-400">Trace ID: </span>
            <span className="text-white font-mono">{trace.id.slice(0, 12)}...</span>
          </div>
          <div>
            <span className="text-gray-400">状态: </span>
            <Tag color={trace.status === 'completed' ? 'green' : trace.status === 'failed' ? 'red' : 'blue'}>
              {trace.status}
            </Tag>
          </div>
          <div>
            <span className="text-gray-400">Tokens: </span>
            <span className="text-white">{trace.total_tokens ?? '—'}</span>
          </div>
          <div>
            <span className="text-gray-400">耗时: </span>
            <span className="text-white">{trace.total_latency_ms ? `${trace.total_latency_ms}ms` : '—'}</span>
          </div>
        </div>
        {rawTrace?.query && (
          <div className="mt-3 pt-3 border-t border-gray-700">
            <span className="text-gray-400">Query: </span>
            <span className="text-white">{rawTrace.query}</span>
          </div>
        )}
      </Card>

      {rawTrace ? (
        <div className="grid grid-cols-2 gap-4">
          <Card title={<span className="text-white">节点列表</span>} className="bg-[#1e293b]">
            <div className="space-y-2 max-h-[500px] overflow-auto">
              {rawTrace.nodes.map((node) => (
                <div
                  key={node.node_id}
                  className={`p-3 rounded cursor-pointer transition-all ${
                    selectedNodeId === node.node_id
                      ? 'bg-[#1e3a5f] border-l-[3px] border-l-blue-500'
                      : 'bg-[#0f172a] hover:bg-[#1e3a5f]/50'
                  }`}
                  onClick={() => setSelectedNodeId(node.node_id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {statusIcons[node.status]}
                      <span className="text-white font-medium">{node.node_name}</span>
                      {node.card_type && (
                        <Tag color="blue" className="text-xs">{node.card_type}</Tag>
                      )}
                    </div>
                    <div className="text-gray-400 text-xs">
                      {node.latency_ms}ms · {node.tokens_used} tokens
                    </div>
                  </div>
                  <div className="text-gray-400 text-sm mt-1 truncate">
                    {node.output_summary}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card title={<span className="text-white">节点详情</span>} className="bg-[#1e293b]">
            {selectedNode ? (
              <div>
                <div className="flex items-center gap-2 mb-4 pb-3 border-b border-gray-700">
                  {statusIcons[selectedNode.status]}
                  <span className="text-white font-medium text-lg">{selectedNode.node_name}</span>
                  {selectedNode.card_type && (
                    <Tag color="blue">{selectedNode.card_type}</Tag>
                  )}
                </div>
                <NodeDetailPanel node={selectedNode} />
              </div>
            ) : (
              <div className="text-gray-400 text-center py-12">
                ← 点击左侧节点查看详情
              </div>
            )}
          </Card>
        </div>
      ) : (
        <Card className="bg-[#1e293b]">
          <div className="text-gray-400 text-center py-8">暂无 Trace 数据</div>
        </Card>
      )}
    </div>
  );
}
