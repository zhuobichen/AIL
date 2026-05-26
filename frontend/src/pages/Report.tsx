import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTaskResults } from '@/api/client';
import ReactECharts from 'echarts-for-react';
import { Loader2, ArrowLeft, Users, Zap, Award } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Report() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!taskId) return;
    getTaskResults(taskId).then(data => {
      setResults(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [taskId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
      </div>
    );
  }

  if (!results) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950 text-white">
        暂无数据，请检查任务 ID
      </div>
    );
  }

  const { network_analysis, destiny_predictions } = results;
  const graphData = network_analysis.graph_data;

  // 转换 NetworkX JSON 为 ECharts 格式
  const nodes = graphData.nodes.map((node: any) => ({
    id: node.id,
    name: node.id,
    symbolSize: Math.max(20, (network_analysis.degree_centrality[node.id] || 0) * 100),
    category: network_analysis.communities.findIndex((c: string[]) => c.includes(node.id)),
    itemStyle: {
      borderColor: node.id === network_analysis.main_character ? '#22d3ee' : 'transparent',
      borderWidth: node.id === network_analysis.main_character ? 4 : 0,
      shadowBlur: 10,
      shadowColor: 'rgba(0,0,0,0.5)'
    }
  }));

  const links = graphData.links.map((link: any) => ({
    source: link.source,
    target: link.target,
    value: link.weight || 1,
    lineStyle: { width: Math.sqrt(link.weight || 1) }
  }));

  const categories = network_analysis.communities.map((_: any, i: number) => ({ name: `社区 ${i+1}` }));

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item' },
    legend: { textStyle: { color: '#9ca3af' }, bottom: 0 },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes,
        links: links,
        categories: categories,
        roam: true,
        label: {
          show: true,
          position: 'right',
          color: '#e5e7eb',
          fontSize: 14,
        },
        force: {
          repulsion: 300,
          edgeLength: 100,
          gravity: 0.1
        },
        lineStyle: {
          color: 'source',
          curveness: 0.3,
          opacity: 0.7
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 5 }
        }
      }
    ],
    color: ['#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#3b82f6']
  };

  const topCharacters = Object.entries(network_analysis.degree_centrality)
    .sort(([,a]: any, [,b]: any) => b - a)
    .slice(0, 8);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header */}
        <motion.div 
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="flex items-center justify-between"
        >
          <div>
            <button 
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-gray-400 hover:text-cyan-400 transition-colors mb-4 text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4" /> 返回首页
            </button>
            <h1 className="text-4xl font-black text-white flex items-center gap-4">
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-500">
                世界观全景解析报告
              </span>
            </h1>
            <p className="text-gray-400 mt-2 text-lg">基于 {graphData.nodes.length} 名角色和 {graphData.links.length} 段关系连接</p>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Graph (takes up 2 columns) */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2 bg-gray-900/40 backdrop-blur-md border border-gray-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500" />
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-100">
              <Users className="w-5 h-5 text-cyan-400" /> 社交网络拓扑图
            </h2>
            <div className="h-[600px] w-full">
              <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
            </div>
          </motion.div>

          {/* Side Panels */}
          <div className="space-y-8">
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-gray-900/40 backdrop-blur-md border border-gray-800 rounded-3xl p-6 shadow-xl"
            >
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-100">
                <Zap className="w-5 h-5 text-yellow-400" /> 核心枢纽人物 (Top 8)
              </h2>
              <div className="space-y-4">
                {topCharacters.map(([name, deg]: any, idx) => (
                  <div key={name} className="flex items-center justify-between group">
                    <div className="flex items-center gap-3">
                      <span className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${idx < 3 ? 'bg-cyan-500/20 text-cyan-400' : 'bg-gray-800 text-gray-400'}`}>
                        {idx + 1}
                      </span>
                      <span className={`font-medium ${name === network_analysis.main_character ? 'text-cyan-400 font-bold' : 'text-gray-300'}`}>
                        {name} {name === network_analysis.main_character && '👑'}
                      </span>
                    </div>
                    <div className="text-sm font-mono text-gray-500 bg-gray-950 px-2 py-1 rounded">
                      {(deg * 100).toFixed(1)}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-gray-900/40 backdrop-blur-md border border-gray-800 rounded-3xl p-6 shadow-xl"
            >
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-100">
                <Award className="w-5 h-5 text-purple-400" /> 命运脉络推演
              </h2>
              <div className="space-y-4 overflow-y-auto max-h-[300px] pr-2 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                {Object.entries(destiny_predictions).slice(0, 4).map(([name, pred]: any) => {
                  const outlook = pred.overall_outlook;
                  const colorClass = outlook === 'positive' ? 'text-green-400 border-green-500/30 bg-green-500/5' : 
                                    outlook === 'negative' ? 'text-red-400 border-red-500/30 bg-red-500/5' : 
                                    'text-yellow-400 border-yellow-500/30 bg-yellow-500/5';
                  return (
                    <div key={name} className={`p-4 rounded-2xl border ${colorClass}`}>
                      <div className="flex justify-between items-center mb-2">
                        <h3 className="font-bold text-lg">{name}</h3>
                        <span className="text-xs font-mono opacity-80 border border-current px-2 py-1 rounded-full">
                          置信度: {pred.overall_confidence.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-sm opacity-90 mb-3 line-clamp-3">{pred.summary}</p>
                      {pred.predictions[0] && (
                        <div className="text-xs opacity-75 flex gap-2">
                          <span className="font-bold">[{pred.predictions[0].category}]</span>
                          <span className="truncate">{pred.predictions[0].description}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </motion.div>
          </div>
        </div>

      </div>
    </div>
  );
}