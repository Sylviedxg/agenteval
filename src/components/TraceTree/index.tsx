import React, { useState } from 'react';
import { Tag, Tooltip } from 'antd';
import {
  RightOutlined,
  DownOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import styles from './index.module.css';

// 节点类型定义
export interface TraceNode {
  id: string;
  name: string;
  type: 'MainAgent' | 'SubAgent' | 'LLM' | 'Tool' | 'Bubble' | 'Gate' | 'SPAN' | 'GENERATION' | 'EVENT';
  duration_ms?: number;
  tokens?: number;
  status?: 'success' | 'error' | 'running';
  children?: TraceNode[];
  metadata?: Record<string, any>;
  input?: string;
  output?: string;
  scores?: Array<{ label: string; value: number; level: 'good' | 'mid' | 'bad' }>;
}

interface TraceTreeProps {
  nodes: TraceNode[];
  selectedId?: string;
  onSelect?: (node: TraceNode) => void;
}

// 类型颜色映射
const typeConfig: Record<string, { bg: string; color: string; label: string }> = {
  MainAgent: { bg: '#E6F4FF', color: '#1677FF', label: 'MainAgent' },
  SubAgent: { bg: '#EEEDFE', color: '#534AB7', label: 'SubAgent' },
  Tool: { bg: '#EAF3DE', color: '#3B6D11', label: 'Tool' },
  LLM: { bg: '#FFF7E6', color: '#D46B08', label: 'LLM' },
  Bubble: { bg: '#FFF1F0', color: '#CF1322', label: '↑ 冒泡' },
  Gate: { bg: '#F6FFED', color: '#389E0D', label: '★Gate' },
  SPAN: { bg: '#F0F0F0', color: '#595959', label: 'Span' },
  GENERATION: { bg: '#FFF7E6', color: '#D46B08', label: 'LLM' },
  EVENT: { bg: '#FFF1F0', color: '#CF1322', label: 'Event' },
};

// 格式化时间
const formatDuration = (ms?: number): string => {
  if (!ms) return '';
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
};

// 格式化token数
const formatTokens = (tokens?: number): string => {
  if (!tokens) return '';
  if (tokens < 1000) return `${tokens}tok`;
  return `${(tokens / 1000).toFixed(1)}k tok`;
};

// 单个节点组件
const TraceNodeItem: React.FC<{
  node: TraceNode;
  depth: number;
  selectedId?: string;
  onSelect?: (node: TraceNode) => void;
}> = ({ node, depth, selectedId, onSelect }) => {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedId === node.id;
  const config = typeConfig[node.type] || typeConfig.SPAN;

  const handleClick = () => {
    onSelect?.(node);
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setExpanded(!expanded);
  };

  return (
    <div className={styles.nodeWrapper}>
      <div
        className={`${styles.nodeRow} ${isSelected ? styles.selected : ''}`}
        onClick={handleClick}
        style={{ paddingLeft: depth * 20 + 8 }}
      >
        {/* 展开/折叠按钮 */}
        <span className={styles.expandBtn} onClick={handleToggle}>
          {hasChildren ? (
            expanded ? <DownOutlined /> : <RightOutlined />
          ) : (
            <span style={{ width: 14 }} />
          )}
        </span>

        {/* 类型标签 */}
        <Tag
          style={{
            background: config.bg,
            color: config.color,
            border: 'none',
            fontSize: 11,
            padding: '2px 7px',
            marginRight: 8,
          }}
        >
          {config.label}
        </Tag>

        {/* 节点名称 */}
        <span className={styles.nodeName}>{node.name}</span>

        {/* 元信息 */}
        <span className={styles.nodeMeta}>
          {node.duration_ms && (
            <Tooltip title="耗时">
              <span>
                <ClockCircleOutlined style={{ marginRight: 4 }} />
                {formatDuration(node.duration_ms)}
              </span>
            </Tooltip>
          )}
          {node.tokens && (
            <span style={{ marginLeft: 8 }}>{formatTokens(node.tokens)}</span>
          )}
          {node.children && node.children.length > 0 && (
            <span style={{ marginLeft: 8, color: '#8c8c8c' }}>
              {node.children.length} 子节点
            </span>
          )}
        </span>

        {/* 状态指示 */}
        {node.status === 'error' && (
          <Tag color="error" style={{ marginLeft: 8 }}>错误</Tag>
        )}
      </div>

      {/* 子节点 */}
      {hasChildren && expanded && (
        <div className={styles.childrenWrapper}>
          {node.children!.map((child) => (
            <TraceNodeItem
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Trace树组件
const TraceTree: React.FC<TraceTreeProps> = ({ nodes, selectedId, onSelect }) => {
  return (
    <div className={styles.traceTree}>
      {nodes.map((node) => (
        <TraceNodeItem
          key={node.id}
          node={node}
          depth={0}
          selectedId={selectedId}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
};

export default TraceTree;
