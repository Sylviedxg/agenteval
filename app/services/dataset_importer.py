"""
评测集Excel导入服务
解析tanqi_eval_v3.xlsx格式的评测集文件
"""
import io
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd


class DatasetImporter:
    """评测集导入器"""
    
    # 评分等级映射
    SCORE_MAPPING = {
        'H': 1.0,    # High
        'M': 0.7,    # Medium
        'L': 0.4,    # Low
        'N': None,   # Not applicable
    }
    
    def __init__(self):
        self.nodes = []
        self.scenarios = []
        self.cases = []
    
    async def import_from_excel(self, file_content: bytes) -> Dict[str, Any]:
        """
        从Excel文件导入评测集
        
        Args:
            file_content: Excel文件内容
            
        Returns:
            {
                "nodes": [...],      # 评测节点列表
                "scenarios": [...],  # 场景列表
                "cases": [...],      # 测试用例列表
                "summary": {...}     # 导入摘要
            }
        """
        df = pd.read_excel(io.BytesIO(file_content), header=None)
        
        # 解析节点定义（前4列）
        nodes = self._parse_nodes(df)
        
        # 解析场景定义（从第5列开始）
        scenarios = self._parse_scenarios(df)
        
        # 生成测试用例
        cases = self._generate_cases(df, nodes, scenarios)
        
        return {
            "nodes": nodes,
            "scenarios": scenarios,
            "cases": cases,
            "summary": {
                "total_nodes": len(nodes),
                "total_scenarios": len(scenarios),
                "total_cases": len(cases),
                "gate_nodes": sum(1 for n in nodes if n.get("is_gate")),
                "layers": list(set(n["layer"] for n in nodes))
            }
        }
    
    def _parse_nodes(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """解析评测节点定义"""
        nodes = []
        
        # 从第4行开始是节点数据（0-indexed: row 3）
        for idx in range(3, len(df)):
            row = df.iloc[idx]
            
            layer = str(row[0]) if pd.notna(row[0]) else ""
            agent = str(row[1]) if pd.notna(row[1]) else ""
            node_name = str(row[2]) if pd.notna(row[2]) else ""
            is_gate = str(row[3]).strip() == "★Gate" if pd.notna(row[3]) else False
            
            if not node_name or node_name == "nan":
                continue
            
            # 解析层级
            layer_code = "L0"
            if "L0" in layer:
                layer_code = "L0"
            elif "L1" in layer:
                layer_code = "L1"
            elif "L2" in layer:
                layer_code = "L2"
            elif "L3" in layer:
                layer_code = "L3"
            
            # 生成节点编码
            node_code = self._generate_node_code(node_name, agent)
            
            nodes.append({
                "id": str(uuid.uuid4()),
                "code": node_code,
                "name": node_name,
                "agent": agent,
                "layer": layer,
                "layer_code": layer_code,
                "is_gate": is_gate,
                "row_index": idx
            })
        
        return nodes
    
    def _parse_scenarios(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """解析场景定义"""
        scenarios = []
        
        # 第1行是场景分组（row 0）
        # 第2行是场景名称（row 1）
        # 第3行是能力维度（row 2）
        
        header_row = df.iloc[0]
        scenario_row = df.iloc[1]
        capability_row = df.iloc[2]
        
        current_scenario = None
        col_idx = 4  # 从第5列开始
        
        while col_idx < len(df.columns):
            # 检查是否是新场景
            scenario_name = scenario_row[col_idx] if pd.notna(scenario_row[col_idx]) else None
            capability = capability_row[col_idx] if pd.notna(capability_row[col_idx]) else None
            
            if scenario_name and str(scenario_name) != "nan":
                # 解析场景ID和名称
                scenario_str = str(scenario_name).replace("\n", " ").strip()
                parts = scenario_str.split(" ", 1)
                scenario_id = parts[0] if parts else f"S{len(scenarios)+1:02d}"
                scenario_title = parts[1] if len(parts) > 1 else scenario_str
                
                current_scenario = {
                    "id": str(uuid.uuid4()),
                    "code": scenario_id,
                    "name": scenario_title,
                    "capabilities": [],
                    "start_col": col_idx
                }
                scenarios.append(current_scenario)
            
            if current_scenario and capability and str(capability) != "nan":
                # 解析能力维度
                cap_str = str(capability).replace("\n", " ").strip()
                parts = cap_str.split(" ", 1)
                cap_code = parts[0] if parts else f"C{len(current_scenario['capabilities'])+1}"
                cap_name = parts[1] if len(parts) > 1 else cap_str
                
                current_scenario["capabilities"].append({
                    "code": cap_code,
                    "name": cap_name,
                    "col_index": col_idx
                })
            
            col_idx += 1
        
        return scenarios
    
    def _generate_cases(
        self, 
        df: pd.DataFrame, 
        nodes: List[Dict], 
        scenarios: List[Dict]
    ) -> List[Dict[str, Any]]:
        """生成测试用例"""
        cases = []
        
        for scenario in scenarios:
            for cap in scenario.get("capabilities", []):
                col_idx = cap["col_index"]
                
                # 收集该场景+能力维度下各节点的期望评分
                expected_scores = {}
                for node in nodes:
                    row_idx = node["row_index"]
                    score_str = str(df.iloc[row_idx, col_idx]).strip().upper() if pd.notna(df.iloc[row_idx, col_idx]) else "N"
                    
                    if score_str in self.SCORE_MAPPING:
                        expected_scores[node["code"]] = {
                            "level": score_str,
                            "score": self.SCORE_MAPPING[score_str],
                            "node_name": node["name"],
                            "is_gate": node["is_gate"]
                        }
                
                case = {
                    "id": str(uuid.uuid4()),
                    "scenario_id": scenario["id"],
                    "scenario_code": scenario["code"],
                    "scenario_name": scenario["name"],
                    "capability_code": cap["code"],
                    "capability_name": cap["name"],
                    "case_name": f"{scenario['code']}_{cap['code']}",
                    "expected_scores": expected_scores,
                    "input_query": f"[{scenario['name']}] {cap['name']}任务",  # 占位，后续可编辑
                    "expected_output": None,  # 占位
                    "metadata": {
                        "col_index": col_idx,
                        "scenario": scenario["code"],
                        "capability": cap["code"]
                    }
                }
                cases.append(case)
        
        return cases
    
    def _generate_node_code(self, node_name: str, agent: str) -> str:
        """生成节点编码"""
        # 清理名称
        name = node_name.replace("(", "_").replace(")", "").replace("+", "_")
        name = name.replace("→", "_to_").replace("（", "_").replace("）", "")
        
        # 转换为小写下划线格式
        code = ""
        for char in name:
            if char.isalnum() or char == "_":
                code += char.lower()
            elif char in [" ", "-"]:
                code += "_"
        
        # 去除连续下划线
        while "__" in code:
            code = code.replace("__", "_")
        
        return code.strip("_")


# 单例
dataset_importer = DatasetImporter()
