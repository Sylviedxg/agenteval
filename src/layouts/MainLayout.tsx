import { Layout, Menu } from 'antd';
import type { MenuProps } from 'antd';
import {
  DashboardOutlined,
  ExperimentOutlined,
  BugOutlined,
  SettingOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

const { Sider, Content } = Layout;

type MenuItem = Required<MenuProps>['items'][number];

const menuItems: MenuItem[] = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: '总览',
  },
  {
    key: '/experiments',
    icon: <ExperimentOutlined />,
    label: '实验',
  },
  {
    key: '/badcases',
    icon: <BugOutlined />,
    label: 'BadCase',
  },
  {
    key: '/config',
    icon: <SettingOutlined />,
    label: '配置',
    children: [
      {
        key: '/config/products',
        label: '产品配置',
      },
      {
        key: '/config/metrics',
        label: '指标库',
      },
      {
        key: '/config/datasets',
        label: '评测集',
      },
    ],
  },
  {
    key: '/changelog',
    icon: <HistoryOutlined />,
    label: '变更记录',
  },
];

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key);
  };

  const getSelectedKeys = () => {
    const path = location.pathname;
    if (path.startsWith('/config/')) {
      return [path];
    }
    return [path === '' ? '/' : path];
  };

  const getOpenKeys = () => {
    if (location.pathname.startsWith('/config')) {
      return ['/config'];
    }
    return [];
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        width={220}
        style={{
          background: '#0f172a',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid #1e293b',
          }}
        >
          <span
            style={{
              color: '#fff',
              fontSize: 14,
              fontWeight: 600,
              letterSpacing: '0.2em',
            }}
          >
            AgentEval
          </span>
        </div>
        <Menu
          mode="inline"
          selectedKeys={getSelectedKeys()}
          defaultOpenKeys={getOpenKeys()}
          items={menuItems}
          onClick={handleMenuClick}
          style={{
            background: '#0f172a',
            borderRight: 'none',
          }}
          theme="dark"
        />
      </Sider>
      <Layout style={{ marginLeft: 220, background: '#0f172a' }}>
        <Content
          style={{
            padding: 24,
            minHeight: '100vh',
            background: '#0f172a',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
