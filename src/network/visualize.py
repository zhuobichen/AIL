"""人物关系网络可视化

支持 matplotlib 静态图和 PyVis 交互式图两种输出方式。
"""

import os
from typing import Any, Optional
import networkx as nx


class NetworkVisualizer:
    """网络可视化器

    使用 matplotlib 生成静态图，PyVis 生成交互式 HTML 图。
    """

    def __init__(self, network_builder=None):
        """
        Args:
            network_builder: CharacterNetworkBuilder 实例
        """
        self.builder = network_builder
        self.G: nx.Graph | None = (
            network_builder.G if network_builder else None
        )

    def set_graph(self, G: nx.Graph):
        """设置要可视化的图"""
        self.G = G

    def to_matplotlib(
        self,
        output_path: Optional[str] = None,
        figsize: tuple[int, int] = (14, 10),
        title: str = "人物关系网络",
        show_labels: bool = True,
    ):
        """使用 matplotlib 绘制静态网络图

        Args:
            output_path: 输出文件路径（不指定则显示）
            figsize: 画布大小
            title: 图标题
            show_labels: 是否显示标签
        """
        import matplotlib.pyplot as plt

        if self.G is None or self.G.number_of_nodes() == 0:
            raise ValueError("图为空，请先 build_network")

        G = self.G

        plt.figure(figsize=figsize)

        # 布局
        pos = nx.spring_layout(G, k=3, iterations=50, seed=42)

        # 计算节点大小（基于度中心性）
        degree_cent = nx.degree_centrality(G)
        node_sizes = [degree_cent.get(node, 0.1) * 3000 + 300 for node in G.nodes()]

        # 节点颜色基于社区
        try:
            communities = list(nx.community.greedy_modularity_communities(G))
            community_map: dict[str, int] = {}
            for i, comm in enumerate(communities):
                for node in comm:
                    community_map[node] = i
            node_colors = [community_map.get(node, 0) for node in G.nodes()]
        except Exception:
            node_colors = [0] * G.number_of_nodes()

        # 边的粗细基于权重
        edge_widths = [
            G[u][v].get("weight", 1) * 1.5 for u, v in G.edges()
        ]

        # 绘制
        nx.draw_networkx_nodes(
            G, pos,
            node_size=node_sizes,
            node_color=node_colors,
            cmap=plt.cm.Set3,
            alpha=0.85,
        )

        nx.draw_networkx_edges(
            G, pos,
            width=edge_widths,
            alpha=0.4,
            edge_color="#888888",
            style="solid",
        )

        if show_labels:
            nx.draw_networkx_labels(
                G, pos,
                font_size=11,
                font_family="SimHei",
            )

        plt.title(title, fontsize=16, fontfamily="SimHei")
        plt.axis("off")
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()
            return output_path
        else:
            plt.show()
            return None

    def to_standalone_html(
        self,
        output_path: str = "character_network.html",
        height: str = "700px",
        width: str = "100%",
        bgcolor: str = "#f5f5f5",
        title: str = "人物关系网络",
    ) -> str:
        """生成完全自包含的 HTML 交互式网络图（零外部依赖）

        将 vis-network JS/CSS 内嵌到 HTML 中，无需任何 CDN 即可离线查看。

        Args:
            output_path: HTML 输出路径
            height: 画布高度
            width: 画布宽度
            bgcolor: 背景色
            title: 页面标题

        Returns:
            输出文件路径
        """
        if self.G is None or self.G.number_of_nodes() == 0:
            raise ValueError("图为空，请先 build_network")

        G = self.G
        degree_cent = nx.degree_centrality(G)

        # 构建节点
        nodes_json = []
        for node in G.nodes():
            size = int(degree_cent.get(node, 0.1) * 30 + 8)
            nodes_json.append({
                "id": node,
                "label": node,
                "size": size,
                "title": f"<b>{node}</b><br>度中心性: {degree_cent.get(node, 0):.3f}",
            })

        # 构建边
        edges_json = []
        for u, v, data in G.edges(data=True):
            weight = data.get("weight", 1)
            types = data.get("types", ["association"])
            edges_json.append({
                "from": u,
                "to": v,
                "value": weight,
                "title": f"关系: {', '.join(types)}<br>权重: {weight}",
            })

        # 生成内嵌 vis-network 的独立 HTML
        html = self._build_standalone_html(
            nodes_json, edges_json, height, width, bgcolor, title
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return os.path.abspath(output_path)

    def _build_standalone_html(
        self,
        nodes: list,
        edges: list,
        height: str,
        width: str,
        bgcolor: str,
        title: str,
    ) -> str:
        """构建自包含 HTML（内嵌 vis-network JS/CSS）"""
        import base64
        import json as jmod

        # 读取本地 vis-network JS（从 unpkg 下载的）
        js_code = "// vis-network placeholder"
        css_code = "/* vis-network placeholder */"

        # 尝试从 examples 目录加载 JS/CSS
        lib_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))
        examples_dir = os.path.join(lib_dir, "examples")
        js_path = os.path.join(examples_dir, "vis-network.min.js")
        css_path = os.path.join(examples_dir, "vis-network.min.css")

        try:
            with open(js_path, "r", encoding="utf-8") as f:
                js_code = f.read()
        except FileNotFoundError:
            pass

        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_code = f.read()
        except FileNotFoundError:
            pass

        nodes_str = jmod.dumps(nodes, ensure_ascii=False)
        edges_str = jmod.dumps(edges, ensure_ascii=False)

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: {bgcolor}; }}
  #header {{
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    color: white; padding: 16px 24px; display: flex;
    justify-content: space-between; align-items: center;
  }}
  #header h1 {{ font-size: 20px; font-weight: 500; }}
  #header .stats {{ font-size: 13px; opacity: 0.8; }}
  #mnt {{ width: {width}; height: {height}; background: white; }}
  #legend {{
    position: absolute; bottom: 16px; left: 16px;
    background: rgba(255,255,255,0.9); border-radius: 8px;
    padding: 10px 14px; font-size: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; margin: 4px 0; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
</style>
{css_code}
</head>
<body>
<div id="header">
  <h1>{title}</h1>
  <div class="stats">
    人物: {len(nodes)} &nbsp;|&nbsp; 关系: {len(edges)} &nbsp;|&nbsp;
    主角: {nodes[0]['id'] if nodes else '-'}
  </div>
</div>
<div style="position: relative;">
  <div id="mnt"></div>
  <div id="legend">
    <div style="font-weight:bold;margin-bottom:4px;">操作提示</div>
    <div style="color:#666;font-size:11px;">🖱 滚轮缩放 &nbsp;|&nbsp; 拖拽移动</div>
    <div style="color:#666;font-size:11px;">点击节点查看详情</div>
  </div>
</div>

<script>
{js_code}
</script>
<script>
(function() {{
  var nodes = new vis.DataSet({nodes_str});
  var edges = new vis.DataSet({edges_str});
  var container = document.getElementById('mnt');
  var data = {{ nodes: nodes, edges: edges }};
  var options = {{
    physics: {{
      barnesHut: {{
        gravitationalConstant: -2000,
        centralGravity: 0.3,
        springLength: 180,
        springConstant: 0.04,
        damping: 0.09
      }},
      minVelocity: 0.75
    }},
    nodes: {{
      font: {{ size: 14, face: 'Microsoft YaHei' }},
      borderWidth: 1,
      borderWidthSelected: 2,
      color: {{ background: '#4A90D9', border: '#2E5C8A',
                highlight: {{ background: '#F5A623', border: '#C17E1A' }} }},
    }},
    edges: {{
      width: 1.5,
      color: {{ color: '#ccc', highlight: '#F5A623' }},
      smooth: {{ type: 'continuous' }},
    }},
    interaction: {{
      hover: true,
      tooltipDelay: 100,
      zoomView: true,
      dragView: true,
    }},
  }};
  new vis.Network(container, data, options);
}})();
</script>
</body>
</html>"""


    def to_cytoscape_elements(self) -> list[dict[str, Any]]:
        """导出为 Cytoscape.js 格式的 elements

        Returns:
            Cytoscape.js elements 列表
        """
        if self.G is None:
            return []

        elements = []
        for node in self.G.nodes():
            elements.append({"data": {"id": node, "label": node}})

        for u, v, data in self.G.edges(data=True):
            elements.append({
                "data": {
                    "id": f"{u}-{v}",
                    "source": u,
                    "target": v,
                    "weight": data.get("weight", 1),
                    "types": ",".join(data.get("types", [])),
                }
            })

        return elements

    def to_d3_json(self) -> dict[str, Any]:
        """导出为 D3.js 力导向图格式的 JSON

        Returns:
            {"nodes": [...], "links": [...]}
        """
        if self.G is None:
            return {"nodes": [], "links": []}

        nodes = [{"id": n, "name": n, "top_locations": self.G.nodes[n].get("top_locations", [])} for n in self.G.nodes()]
        links = [
            {
                "source": u,
                "target": v,
                "weight": d.get("weight", 1),
                "types": d.get("types", []),
                "sentiment": d.get("sentiment", "neutral"),
                "context_snippet": d.get("context_snippet", ""),
                "contexts": d.get("contexts", [])
            }
            for u, v, d in self.G.edges(data=True)
        ]

        return {"nodes": nodes, "links": links}
