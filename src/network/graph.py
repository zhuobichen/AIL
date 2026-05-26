"""人物社交网络构建与分析"""

from typing import Any, List
from collections import Counter
import networkx as nx

from ..models import Relation, NetworkStats

class CharacterNetworkBuilder:
    """人物社交网络构建器

    基于关系数据构建人物社交网络图，并提供中心性分析、社区检测等功能。
    """

    def __init__(self):
        self.G: nx.Graph | None = None

    def build_network(self, relations: List[Relation]) -> nx.Graph:
        """从关系列表构建社交网络

        Args:
            relations: RelationshipExtractor 输出的 Relation 对象列表

        Returns:
            NetworkX 图对象
        """
        G = nx.Graph()

        for rel in relations:
            source = rel.source
            target = rel.target
            rel_type = rel.type

            if G.has_edge(source, target):
                # 累加权重
                G[source][target]["weight"] += 1
                # 追加关系类型
                if rel_type not in G[source][target]["types"]:
                    G[source][target]["types"].append(rel_type)
            else:
                G.add_edge(
                    source,
                    target,
                    weight=1,
                    types=[rel_type],
                )

        self.G = G
        return G

    def analyze_network(self) -> NetworkStats:
        """分析网络特征

        Returns:
            NetworkStats 对象，包含网络指标
        """
        if self.G is None or self.G.number_of_nodes() == 0:
            return NetworkStats(
                num_characters=0,
                num_relations=0,
                density=0.0
            )

        G = self.G

        # 度中心性（谁认识的人多）
        degree_cent = nx.degree_centrality(G)

        # 介数中心性（谁是信息桥梁）
        betweenness_cent = nx.betweenness_centrality(G)

        # 社区检测
        try:
            communities_raw = list(nx.community.greedy_modularity_communities(G))
            communities = [list(c) for c in communities_raw]
        except Exception:
            communities = []

        # 关键人物
        main_char = max(degree_cent, key=degree_cent.get) if degree_cent else None
        bridge_char = max(betweenness_cent, key=betweenness_cent.get) if betweenness_cent else None

        return NetworkStats(
            num_characters=G.number_of_nodes(),
            num_relations=G.number_of_edges(),
            density=nx.density(G),
            main_character=main_char,
            bridge_character=bridge_char,
            communities=communities,
            degree_centrality=degree_cent,
            betweenness_centrality=betweenness_cent
        )

    def get_ego_network(self, character: str, radius: int = 1) -> nx.Graph:
        """获取某人物的自我网络（邻域子图）

        Args:
            character: 人物名
            radius: 邻域半径（跳数）

        Returns:
            子图
        """
        if self.G is None:
            raise ValueError("请先调用 build_network")

        nodes = set([character])
        current_layer = set([character])

        for _ in range(radius):
            next_layer = set()
            for node in current_layer:
                next_layer.update(self.G.neighbors(node))
            nodes.update(next_layer)
            current_layer = next_layer

        return self.G.subgraph(nodes)

    def get_character_stats(self, character: str) -> dict[str, Any]:
        """获取单个人物的网络统计

        Args:
            character: 人物名

        Returns:
            人物网络指标
        """
        if self.G is None:
            raise ValueError("请先调用 build_network")

        if character not in self.G:
            return {"error": f"人物 '{character}' 不在网络中"}

        return {
            "name": character,
            "degree": self.G.degree(character),
            "neighbors": list(self.G.neighbors(character)),
            "num_neighbors": len(list(self.G.neighbors(character))),
            "edge_types": self._summarize_edge_types(character),
        }

    def _summarize_edge_types(self, character: str) -> Counter:
        """汇总某人物所有边的类型"""
        types_counter: Counter = Counter()
        if self.G is None:
            return types_counter

        for neighbor in self.G.neighbors(character):
            edge_data = self.G[character][neighbor]
            for t in edge_data.get("types", []):
                types_counter[t] += 1

        return types_counter
