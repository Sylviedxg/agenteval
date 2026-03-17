import { useState, useEffect } from 'react';
import { Card, Tabs, Table, Tag, Button, Space, Modal, Form, Input, Select, InputNumber, message, Badge, Tooltip, Empty } from 'antd';
import { PlusOutlined, ReloadOutlined, SettingOutlined, CheckCircleOutlined, ClockCircleOutlined, ExperimentOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { 
  getOverview, 
  getDefinitions, 
  createDefinition, 
  initBuiltinMetrics,
  type MetricDefinition, 
  type MetricCategory,
  type Milestone,
  type MetricSystemOverview 
} from '../../../api/metrics';

const { TabPane } = Tabs;
const { TextArea } = Input;

// 层级标签颜色
const levelColors: Record<string, string> = {
  system: 'blue',
  collaboration: 'green',
  agent: 'orange',
};

// 层级名称
const levelNames: Record<string, string> = {
  system: '系统层',
  collaboration: '协作层',
  agent: '单体层',
};

// 指标类型标签
const metricTypeLabels: Record<string, { text: string; color: string }> = {
  process: { text: '过程指标', color: 'cyan' },
  result: { text: '结果指标', color: 'purple' },
};

// 评分方式标签
const scoringMethodLabels: Record<string, { text: string; color: string }> = {
  auto: { text: '自动', color: 'green' },
  manual: { text: '人工', color: 'orange' },
  hybrid: { text: '混合', color: 'blue' },
};

// 采集方式标签
const collectionMethodLabels: Record<string, string> = {
  langfuse: 'Langfuse',
  api: 'API',
  manual: '人工录入',
  computed: '计算得出',
};

// 检查点类型图标
const checkpointIcons: Record<string, React.ReactNode> = {
  entry: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  process: <ClockCircleOutlined style={{ color: '#1890ff' }} />,
  output: <ExperimentOutlined style={{ color: '#722ed1' }} />,
  exit: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
};

export default function Metrics() {
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState<MetricSystemOverview | null>(null);
  const [definitions, setDefinitions] = useState<MetricDefinition[]>([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const [overviewRes, definitionsRes] = await Promise.all([
        getOverview(),
        getDefinitions(),
      ]);
      setOverview(overviewRes.data);
      setDefinitions(definitionsRes.data);
    } catch (error) {
      console.error('加载指标数据失败:', error);
      message.error('加载指标数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 初始化内置指标
  const handleInitBuiltin = async () => {
    try {
      const res = await initBuiltinMetrics();
      if (res.data.initialized) {
        message.success('内置指标初始化成功');
        loadData();
      } else {
        message.info(res.data.message);
      }
    } catch (error) {
      console.error('初始化失败:', error);
      message.error('初始化失败');
    }
  };

  // 创建指标
  const handleCreate = async (values: Partial<MetricDefinition>) => {
    try {
      await createDefinition(values);
      message.success('创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      loadData();
    } catch (error) {
      console.error('创建失败:', error);
      message.error('创建失败');
    }
  };

  // 分类卡片内的简化表格列
  const compactMetricColumns: ColumnsType<MetricDefinition> = [
    {
      title: '指标',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Tooltip title={record.description}>
          <div>
            <div className="font-medium text-white">{text}</div>
            <code className="text-xs text-gray-400">{record.code}</code>
          </div>
        </Tooltip>
      ),
    },
    {
      title: '类型',
      dataIndex: 'metric_type',
      key: 'metric_type',
      width: 80,
      render: (type) => {
        const label = metricTypeLabels[type];
        return label ? <Tag color={label.color} className="text-xs">{label.text}</Tag> : type;
      },
    },
    {
      title: '采集',
      dataIndex: 'collection_method',
      key: 'collection_method',
      width: 80,
      render: (method) => (
        <span className="text-xs text-gray-400">{collectionMethodLabels[method] || method}</span>
      ),
    },
  ];

  // 全部指标页的完整表格列
  const fullMetricColumns: ColumnsType<MetricDefinition> = [
    {
      title: '指标名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text, record) => (
        <Tooltip title={record.description}>
          <span className="font-medium">{text}</span>
        </Tooltip>
      ),
    },
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
      width: 140,
      render: (text) => <code className="text-xs bg-gray-700 px-1 rounded">{text}</code>,
    },
    {
      title: '类型',
      dataIndex: 'metric_type',
      key: 'metric_type',
      width: 90,
      render: (type) => {
        const label = metricTypeLabels[type];
        return label ? <Tag color={label.color}>{label.text}</Tag> : type;
      },
    },
    {
      title: '评分方式',
      dataIndex: 'scoring_method',
      key: 'scoring_method',
      width: 80,
      render: (method) => {
        const label = scoringMethodLabels[method];
        return label ? <Tag color={label.color}>{label.text}</Tag> : method;
      },
    },
    {
      title: '采集方式',
      dataIndex: 'collection_method',
      key: 'collection_method',
      width: 90,
      render: (method) => collectionMethodLabels[method] || method,
    },
    {
      title: '权重',
      dataIndex: 'weight',
      key: 'weight',
      width: 60,
      render: (weight) => weight.toFixed(1),
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
      width: 50,
      render: (unit) => unit || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_builtin',
      key: 'is_builtin',
      width: 70,
      render: (isBuiltin) => (
        <Tag color={isBuiltin ? 'default' : 'blue'}>
          {isBuiltin ? '内置' : '自定义'}
        </Tag>
      ),
    },
  ];

  // 渲染分类卡片
  const renderCategoryCard = (category: MetricCategory) => (
    <Card 
      key={category.id} 
      size="small" 
      className="mb-3 bg-gray-800 border-gray-700"
      title={
        <div className="flex items-center justify-between">
          <span className="text-white">{category.name}</span>
          <Badge count={category.metrics?.length || 0} style={{ backgroundColor: '#1890ff' }} />
        </div>
      }
    >
      {category.description && (
        <p className="text-gray-400 text-sm mb-2">{category.description}</p>
      )}
      {category.metrics && category.metrics.length > 0 ? (
        <Table
          dataSource={category.metrics}
          columns={compactMetricColumns}
          rowKey="id"
          size="small"
          pagination={false}
          className="metrics-table"
        />
      ) : (
        <Empty description="暂无指标" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Card>
  );

  // 渲染里程碑列表
  const renderMilestones = (milestones: Milestone[]) => (
    <div className="space-y-2">
      {milestones.map((milestone, index) => (
        <div 
          key={milestone.id} 
          className="flex items-center p-3 bg-gray-800 rounded-lg border border-gray-700"
        >
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-700 mr-3">
            {checkpointIcons[milestone.checkpoint_type] || index + 1}
          </div>
          <div className="flex-1">
            <div className="flex items-center">
              <span className="font-medium text-white mr-2">{milestone.name}</span>
              <Tag>{milestone.checkpoint_type}</Tag>
            </div>
            {milestone.description && (
              <p className="text-gray-400 text-sm mt-1">{milestone.description}</p>
            )}
            {milestone.related_metrics && milestone.related_metrics.length > 0 && (
              <div className="mt-1">
                <span className="text-gray-500 text-xs mr-2">关联指标:</span>
                {milestone.related_metrics.map((code: string) => (
                  <Tag key={code} className="text-xs">{code}</Tag>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">指标库</h1>
          <p className="text-gray-400 mt-1">
            三层评测体系：系统层 → 协作层 → 单体层，过程指标优先于结果指标
          </p>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
            刷新
          </Button>
          <Button icon={<SettingOutlined />} onClick={handleInitBuiltin}>
            初始化内置指标
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
            新建指标
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card className="bg-gray-800 border-gray-700">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400">{overview?.total_metrics || 0}</div>
            <div className="text-gray-400 mt-1">指标总数</div>
          </div>
        </Card>
        <Card className="bg-gray-800 border-gray-700">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400">{overview?.total_milestones || 0}</div>
            <div className="text-gray-400 mt-1">里程碑检查点</div>
          </div>
        </Card>
        <Card className="bg-gray-800 border-gray-700">
          <div className="text-center">
            <div className="text-3xl font-bold text-cyan-400">
              {definitions.filter(d => d.metric_type === 'process').length}
            </div>
            <div className="text-gray-400 mt-1">过程指标</div>
          </div>
        </Card>
        <Card className="bg-gray-800 border-gray-700">
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-400">
              {definitions.filter(d => d.metric_type === 'result').length}
            </div>
            <div className="text-gray-400 mt-1">结果指标</div>
          </div>
        </Card>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="体系概览" key="overview">
          <div className="grid grid-cols-3 gap-6">
            {/* 系统层 */}
            <div>
              <div className="flex items-center mb-4">
                <Tag color={levelColors.system} className="text-base px-3 py-1">
                  {levelNames.system}
                </Tag>
                <span className="text-gray-400 ml-2">端到端性能与可靠性</span>
              </div>
              {overview?.system_level.map(renderCategoryCard)}
            </div>

            {/* 协作层 */}
            <div>
              <div className="flex items-center mb-4">
                <Tag color={levelColors.collaboration} className="text-base px-3 py-1">
                  {levelNames.collaboration}
                </Tag>
                <span className="text-gray-400 ml-2">多Agent协作质量</span>
              </div>
              {overview?.collaboration_level.map(renderCategoryCard)}
            </div>

            {/* 单体层 */}
            <div>
              <div className="flex items-center mb-4">
                <Tag color={levelColors.agent} className="text-base px-3 py-1">
                  {levelNames.agent}
                </Tag>
                <span className="text-gray-400 ml-2">单个Agent执行质量</span>
              </div>
              {overview?.agent_level.map(renderCategoryCard)}
            </div>
          </div>
        </TabPane>

        <TabPane tab="里程碑检查点" key="milestones">
          <Card className="bg-gray-800 border-gray-700">
            <p className="text-gray-400 mb-4">
              里程碑检查点用于评测关键节点，按执行顺序排列：入口 → 过程 → 输出 → 出口
            </p>
            {overview?.milestones && overview.milestones.length > 0 ? (
              renderMilestones(overview.milestones)
            ) : (
              <Empty description="暂无里程碑" />
            )}
          </Card>
        </TabPane>

        <TabPane tab="全部指标" key="all">
          <Card className="bg-gray-800 border-gray-700">
            <Table
              dataSource={definitions}
              columns={fullMetricColumns}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 20 }}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 创建指标弹窗 */}
      <Modal
        title="新建指标"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{
            metric_type: 'process',
            scoring_method: 'manual',
            data_type: 'score',
            collection_method: 'manual',
            aggregation_method: 'avg',
            weight: 1.0,
            score_range_min: 0,
            score_range_max: 10,
          }}
        >
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="name" label="指标名称" rules={[{ required: true }]}>
              <Input placeholder="如：任务完成度" />
            </Form.Item>
            <Form.Item name="code" label="指标编码" rules={[{ required: true }]}>
              <Input placeholder="如：task_completion" />
            </Form.Item>
          </div>

          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="指标的详细描述" />
          </Form.Item>

          <div className="grid grid-cols-3 gap-4">
            <Form.Item name="metric_type" label="指标类型" rules={[{ required: true }]}>
              <Select>
                <Select.Option value="process">过程指标</Select.Option>
                <Select.Option value="result">结果指标</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="scoring_method" label="评分方式" rules={[{ required: true }]}>
              <Select>
                <Select.Option value="auto">自动</Select.Option>
                <Select.Option value="manual">人工</Select.Option>
                <Select.Option value="hybrid">混合</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="collection_method" label="采集方式">
              <Select>
                <Select.Option value="langfuse">Langfuse</Select.Option>
                <Select.Option value="api">API</Select.Option>
                <Select.Option value="manual">人工录入</Select.Option>
                <Select.Option value="computed">计算得出</Select.Option>
              </Select>
            </Form.Item>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <Form.Item name="data_type" label="数据类型">
              <Select>
                <Select.Option value="number">数值</Select.Option>
                <Select.Option value="percentage">百分比</Select.Option>
                <Select.Option value="duration">时长</Select.Option>
                <Select.Option value="boolean">布尔</Select.Option>
                <Select.Option value="score">评分</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item name="unit" label="单位">
              <Input placeholder="如：ms、%" />
            </Form.Item>
            <Form.Item name="weight" label="权重">
              <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="aggregation_method" label="聚合方式">
              <Select>
                <Select.Option value="avg">平均值</Select.Option>
                <Select.Option value="sum">求和</Select.Option>
                <Select.Option value="max">最大值</Select.Option>
                <Select.Option value="min">最小值</Select.Option>
                <Select.Option value="last">最新值</Select.Option>
                <Select.Option value="count">计数</Select.Option>
              </Select>
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
