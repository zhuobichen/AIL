import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTaskResults, API_BASE_URL } from '@/api/client';
import ReactECharts from 'echarts-for-react';
import { Loader2, ArrowLeft, Users, Zap, Award, MessageSquare, Play, Pause, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Report() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // 时间轴控制状态
  const [currentStage, setCurrentStage] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // RAG 聊天状态
  const [chatQuery, setChatQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<{role: string, content: string, sources?: any[]}[]>([]);
  const [isChatting, setIsChatting] = useState(false);
  
  // 选中的关系片段
  const [selectedRelation, setSelectedRelation] = useState<any>(null);

  useEffect(() => {
    if (!taskId) return;
    getTaskResults(taskId).then(data => {
      setResults(data);
      if (data?.network_analysis?.temporal_graphs?.length > 0) {
        setCurrentStage(data.network_analysis.temporal_graphs.length - 1);
      }
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
  const temporal_graphs = network_analysis.temporal_graphs || [];
  
  // 决定当前使用哪个图谱数据
  let currentGraphData = network_analysis.graph_data;
  if (temporal_graphs.length > 0 && currentStage >= 0 && currentStage < temporal_graphs.length) {
    currentGraphData = temporal_graphs[currentStage].graph_data;
  }
  
  const handlePlay = () => {
    if (isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current);
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      if (currentStage >= temporal_graphs.length - 1) {
        setCurrentStage(0);
      }
      timerRef.current = setInterval(() => {
        setCurrentStage(prev => {
          if (prev >= temporal_graphs.length - 1) {
            if (timerRef.current) clearInterval(timerRef.current);
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500);
    }
  };

  const handleChat = async () => {
    if (!chatQuery.trim() || isChatting) return;
    
    const query = chatQuery;
    setChatQuery('');
    setChatHistory(prev => [...prev, { role: 'user', content: query }]);
    setIsChatting(true);
    
    try {
      // 从 URL 获取书籍名称，默认假设是第一本书
      const book = "longzu"; 
      
      const res = await fetch(`${API_BASE_URL}/rag/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, book })
      });
      
      const data = await res.json();
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: data.answer,
        sources: data.sources 
      }]);
    } catch (e) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: '抱歉，系统回答时出错。' }]);
    } finally {
      setIsChatting(false);
    }
  };

  const onEvents = {
    'click': (params: any) => {
      if (params.dataType === 'edge') {
        setSelectedRelation({
          source: params.data.source,
          target: params.data.target,
          snippet: params.data.context_snippet || "暂无原文片段",
          sentiment: params.data.sentiment || "neutral"
        });
      }
    }
  };

  // 转换 NetworkX JSON 为 ECharts 格式
  const nodes = currentGraphData.nodes.map((node: any) => ({
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

  const links = currentGraphData.links.map((link: any) => {
    // 根据 sentiment 决定红绿颜色
    let color = 'source';
    if (link.sentiment === 'positive') color = '#10b981'; // 绿
    else if (link.sentiment === 'negative') color = '#ef4444'; // 红
    
    return {
      source: link.source,
      target: link.target,
      value: link.weight || 1,
      context_snippet: link.context_snippet,
      sentiment: link.sentiment,
      lineStyle: { 
        width: Math.sqrt(link.weight || 1) * 2,
        color: color,
        opacity: link.sentiment === 'neutral' ? 0.3 : 0.8
      }
    };
  });

  const categories = network_analysis.communities.map((_: any, i: number) => ({ name: `社区 ${i+1}` }));

  const option = {
    backgroundColor: 'transparent',
    tooltip: { 
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          const s = params.data.sentiment;
          const emoji = s === 'positive' ? '💚' : s === 'negative' ? '💔' : '⚪';
          return `${params.data.source} > ${params.data.target}<br/>权重: ${params.data.value.toFixed(2)} ${emoji}<br/><span style="font-size:12px;color:#aaa">点击连线查看原著溯源</span>`;
        }
        return params.name;
      }
    },
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
          curveness: 0.3
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
          
          {/* 时间轴播放控制 */}
          {temporal_graphs.length > 0 && (
            <div className="flex items-center gap-4 bg-gray-900/50 p-3 rounded-2xl border border-gray-800">
              <button 
                onClick={handlePlay}
                className="p-3 bg-cyan-600 hover:bg-cyan-500 rounded-xl text-white transition-colors"
              >
                {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              </button>
              <div className="flex flex-col w-48">
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>剧情演化</span>
                  <span>{currentStage >= 0 ? temporal_graphs[currentStage].progress_percent : 100}%</span>
                </div>
                <input 
                  type="range" 
                  min={0} 
                  max={temporal_graphs.length - 1} 
                  value={currentStage >= 0 ? currentStage : temporal_graphs.length - 1}
                  onChange={(e) => {
                    if (isPlaying) handlePlay(); // 暂停播放
                    setCurrentStage(parseInt(e.target.value));
                  }}
                  className="w-full accent-cyan-500"
                />
              </div>
            </div>
          )}
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
              <ReactECharts option={option} style={{ height: '100%', width: '100%' }} onEvents={onEvents} />
            </div>
            
            {/* 选中关系原文溯源浮层 */}
            <AnimatePresence>
              {selectedRelation && (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  className="absolute bottom-6 left-6 right-6 bg-gray-950/90 backdrop-blur-xl border border-gray-700 p-4 rounded-2xl shadow-2xl"
                >
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-bold text-cyan-400">
                      {selectedRelation.source} ↔ {selectedRelation.target}
                    </h3>
                    <button 
                      onClick={() => setSelectedRelation(null)}
                      className="text-gray-400 hover:text-white"
                    >
                      关闭
                    </button>
                  </div>
                  <p className="text-sm text-gray-300 italic">"{selectedRelation.snippet}"</p>
                </motion.div>
              )}
            </AnimatePresence>
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

            {/* RAG Chat Panel */}
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-gray-900/40 backdrop-blur-md border border-gray-800 rounded-3xl p-6 shadow-xl flex flex-col h-[400px]"
            >
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-100">
                <MessageSquare className="w-5 h-5 text-blue-400" /> 原著知识库问答
              </h2>
              
              <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                {chatHistory.length === 0 ? (
                  <div className="text-sm text-gray-500 text-center mt-10">
                    尝试提问：“楚子航为什么要爆血？”
                  </div>
                ) : (
                  chatHistory.map((msg, i) => (
                    <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-cyan-600 text-white rounded-br-none' : 'bg-gray-800 text-gray-200 rounded-bl-none'}`}>
                        {msg.content}
                      </div>
                    </div>
                  ))
                )}
                {isChatting && (
                  <div className="flex items-start">
                    <div className="bg-gray-800 p-3 rounded-2xl rounded-bl-none text-sm text-gray-400 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" /> 检索原著中...
                    </div>
                  </div>
                )}
              </div>
              
              <div className="relative mt-auto">
                <input 
                  type="text" 
                  value={chatQuery}
                  onChange={e => setChatQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleChat()}
                  placeholder="向原著提问..."
                  disabled={isChatting}
                  className="w-full bg-gray-950 border border-gray-700 rounded-xl py-3 pl-4 pr-12 text-sm focus:outline-none focus:border-cyan-500 text-white"
                />
                <button 
                  onClick={handleChat}
                  disabled={!chatQuery.trim() || isChatting}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-cyan-400 disabled:opacity-50"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          </div>
        </div>

      </div>
    </div>
  );
}