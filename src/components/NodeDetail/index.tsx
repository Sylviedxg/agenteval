import React from 'react';
import { Tag, Empty } from 'antd';
import type { TraceNode } from '../TraceTree';
import styles from './index.module.css';

interface NodeDetailProps {
  node: TraceNode | null;
}

// 类型颜色映射
const typeConfig: Record<string, { bg: string; color: string; label: string }> = {
  MainAgent: { bg: '#E6F4FF', color: '#1677FF', label: 'MainAgent' },
  SubAgent: { bg: '#EEEDFE', color: '#534AB7', label: 'SubAgent' },
  Tool: { bg: '#EAF3DE', color: '#3B6D11', label: 'Tool' },
  LLM: { bg: '#FFF7E6', color: '#D46B08', label: 'LLM' },
  Bubble: { bg: '#FFF1F0', color: '#CF1322', label: '冒泡事件' },
  Gate: { bg: '#F6FFED', color: '#389E0D', label: '★Gate' },
  SPAN: { bg: '#F0F0F0', color: '#595959', label: 'Span' },
  GENERATION: { bg: '#FFF7E6', color: '#D46B08', label: 'LLM Call' },
  EVENT: { bg: '#FFF1F0', color: '#CF1322', label: 'Event' },
};

// 评分等级样式
const getScoreClass = (level: 'good' | 'mid' | 'bad'): string => {
  switch (level) {
    case 'good': return styles.scoreGood;
    case 'mid': return styles.scoreMid;
    case 'bad': return styles.scoreBad;
    default: return styles.scoreMid;
  }
};

// 格式化JSON显示
const formatContent = (content: string | object | undefined): string => {
  if (!content) return '';
  if (typeof content === 'string') return content;
  try {
    return JSON.stringify(content, null, 2);
  } catch {
    return String(content);
  }
};

const NodeDetail: React.FC<NodeDetailProps> = ({ node }) => {
  if (!node) {
    return (
      <div className={styles.detailPanel}>
        <Empty
          description="点击左侧节点查看详情"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    );
  }

  const config = typeConfig[node.type] || typeConfig.SPAN;

  return (
    <div className={styles.detailPanel}>
      {/* 头部：类型 + 名称 */}
      <div className={styles.header}>
        <Tag
          style={{
            background: config.bg,
            color: config.color,
            border: 'none',
            fontSize: 12,
            padding: '3px 10px',
          }}
        >
          {config.label}
        </Tag>
        <span className={styles.nodeName}>{node.name}</span>
      </div>

      {/* 评测得分 */}
      {node.scores && node.scores.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>评测得分</div>
          <div className={styles.scoresWrapper}>
            {node.scores.map((score, idx) => (
              <span
                key={idx}
                className={`${styles.scorePill} ${getScoreClass(score.level)}`}
              >
                {score.label}: {(score.value * 100).toFixed(0)}%
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      {node.input && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>INPUT</div>
          <div className={styles.contentBox}>
            <pre>{formatContent(node.input)}</pre>
          </div>
        </div>
      )}

      {/* Output */}
      {node.output && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>OUTPUT</div>
          <div className={styles.contentBox}>
            <pre>{formatContent(node.output)}</pre>
          </div>
        </div>
      )}

      {/* 元信息 */}
      {node.metadata && Object.keys(node.metadata).length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>
            {node.type === 'Bubble' ? '冒泡内容' : '元信息'}
          </div>
          <div className={styles.contentBox}>
            <pre>{formatContent(node.metadata)}</pre>
          </div>
        </div>
      )}

      {/* 基础信息 */}
      <div className={styles.section}>
        <div className={styles.sectionLabel}>基础信息</div>
        <div className={styles.infoGrid}>
          {node.duration_ms && (
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>耗时</span>
              <span className={styles.infoValue}>
                {node.duration_ms < 1000
                  ? `${node.duration_ms.toFixed(0)}ms`
                  : `${(node.duration_ms / 1000).toFixed(2)}s`}
              </span>
            </div>
          )}
          {node.tokens && (
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>Tokens</span>
              <span className={styles.infoValue}>{node.tokens.toLocaleString()}</span>
            </div>
          )}
          {node.status && (
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>状态</span>
              <Tag color={node.status === 'success' ? 'success' : node.status === 'error' ? 'error' : 'processing'}>
                {node.status === 'success' ? '成功' : node.status === 'error' ? '失败' : '运行中'}
              </Tag>
            </div>
          )}
          {node.children && node.children.length > 0 && (
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>子节点</span>
              <span className={styles.infoValue}>{node.children.length} 个</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NodeDetail;
