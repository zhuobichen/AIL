import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTaskResults, getTaskStatus, API_BASE_URL } from '@/api/client';
import ReactECharts from 'echarts-for-react';
import { Loader2, ArrowLeft, Users, Zap, Award, MessageSquare, Play, Pause, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Report() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [taskStatus, setTaskStatus] = useState<any>(null);
  
  // 时间轴控制状态
  const [currentStage, setCurrentStage] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // RAG 聊天状态
  const [chatQuery, setChatQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<{role: string, content: string, sources?: any[]}[]>([]);
  const [isChatting, setIsChatting] = useState(false);
  
  const [isSandboxOpen, setIsSandboxOpen] = useState(false);
  const [sandboxWhatIf, setSandboxWhatIf] = useState('');
  const [sandboxCharacters, setSandboxCharacters] = useState<string[]>([]);
  const [sandboxResult, setSandboxResult] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  
  const handleRunSimulation = async () => {
    if (!sandboxWhatIf || sandboxCharacters.length < 2) return;
    setIsSimulating(true);
    setSandboxResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/simulation/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: "", // Not used
          book: taskStatus?.book_name || "longzu", 
          task_id: taskId,
          what_if: sandboxWhatIf,
          characters: sandboxCharacters,
          num_turns: 4
        })
      });
      const data = await res.json();
      setSandboxResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };
  
  // 选中的关系片段
  const [selectedRelation, setSelectedRelation] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  useEffect(() => {
    if (!taskId) return;
    Promise.all([
      getTaskResults(taskId),
      getTaskStatus(taskId)
    ]).then(([data, statusData]) => {
      setResults(data);
      setTaskStatus(statusData);
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
      const book = taskStatus?.book_name || "longzu"; 
      
      const res = await fetch(`${API_BASE_URL}/rag/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, book, task_id: taskId })
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
        setSelectedNode(null);
      } else if (params.dataType === 'node') {
        setSelectedNode(params.data);
        setSelectedRelation(null);
      }
    }
  };

  // 转换 NetworkX JSON 为 ECharts 格式
  const nodes = currentGraphData.nodes.map((node: any) => {
    const isLocation = node.type === 'location';
    return {
      id: node.id,
      name: node.id,
      symbolSize: isLocation ? 15 : Math.max(20, (network_analysis.degree_centrality[node.id] || 0) * 100),
      category: network_analysis.communities.findIndex((c: string[]) => c.includes(node.id)),
      symbol: isLocation ? 'square' : 'circle',
      itemStyle: {
        ...(isLocation ? { color: '#eab308' } : {}),
        borderColor: node.id === network_analysis.main_character ? '#22d3ee' : 'transparent',
        borderWidth: node.id === network_analysis.main_character ? 4 : 0,
        shadowBlur: 10,
        shadowColor: 'rgba(0,0,0,0.5)'
      }
    };
  });

  const links = currentGraphData.links.map((link: any) => {
    // 根据 sentiment 决定红绿颜色
    let color = 'source';
    if (link.sentiment === 'positive') color = '#10b981'; // 绿
    else if (link.sentiment === 'negative') color = '#ef4444'; // 红
    else if (link.type === 'location_link') color = '#eab308'; // 黄
    
    return {
      source: link.source,
      target: link.target,
      value: link.weight || 1,
      context_snippet: link.context_snippet,
      sentiment: link.sentiment,
      lineStyle: { 
        width: link.type === 'location_link' ? 1 : Math.sqrt(link.weight || 1) * 2,
        color: color,
        type: link.type === 'location_link' ? 'dashed' : 'solid',
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
            <h1 className="text-4xl font-black text-white flex items-center gap-4 font-serif-sc">
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-500">
                世界观全景解析报告
              </span>
            </h1>
            <p className="text-gray-400 mt-2 text-lg">基于 {currentGraphData.nodes.length} 名角色和 {currentGraphData.links.length} 段关系连接</p>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsSandboxOpen(true)}
              className="px-6 py-3 bg-purple-600/80 hover:bg-purple-500 text-white rounded-2xl shadow-[0_0_15px_rgba(147,51,234,0.3)] flex items-center gap-2 transition-all font-medium neon-border-purple backdrop-blur-md"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
              进入平行沙盘
            </button>

            {/* 时间轴播放控制 */}
            {temporal_graphs.length > 0 && (
              <div className="flex items-center gap-4 glass-panel p-3 rounded-2xl">
                <button 
                  onClick={handlePlay}
                  className="p-3 bg-cyan-600/80 hover:bg-cyan-500 rounded-xl text-white transition-colors backdrop-blur-md"
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
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Graph (takes up 2 columns) */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2 glass-panel rounded-3xl p-6 relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500" />
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-100 font-serif-sc">
              <Users className="w-5 h-5 text-cyan-400" /> 社交网络拓扑图
            </h2>
            <div className="h-[600px] w-full">
              <ReactECharts option={option} style={{ height: '100%', width: '100%' }} onEvents={onEvents} />
            </div>
            
            {/* 节点溯源悬浮窗 */}
            {selectedNode && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute left-8 bottom-8 w-96 glass-panel neon-border-cyan rounded-2xl p-6 z-10"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-3xl font-bold text-white mb-2">{selectedNode.id}</h2>
                    {selectedNode.top_locations && selectedNode.top_locations.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        <span className="text-xs text-gray-400">常去地点:</span>
                        {selectedNode.top_locations.map((loc: string, i: number) => (
                          <span key={i} className="px-2 py-0.5 rounded text-xs bg-gray-800 text-blue-300 border border-gray-700">
                            📍 {loc}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <button 
                    onClick={() => setSelectedNode(null)}
                    className="text-gray-400 hover:text-white"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  </button>
                </div>
              </motion.div>
            )}

            {/* 选中关系原文溯源浮层 */}
            <AnimatePresence>
              {selectedRelation && (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  className="absolute bottom-6 left-6 right-6 glass-panel neon-border-cyan p-4 rounded-2xl"
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
                  <div className="space-y-3 max-h-60 overflow-y-auto custom-scrollbar pr-2">
                    {selectedRelation.contexts?.map((ctx: any, i: number) => (
                      <div key={i} className="text-sm text-gray-300 bg-gray-800/50 p-3 rounded-lg border border-gray-700/50">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`w-2 h-2 rounded-full ${
                            ctx.sentiment === 'positive' ? 'bg-green-500' :
                            ctx.sentiment === 'negative' ? 'bg-red-500' : 'bg-gray-400'
                          }`}></span>
                          {ctx.location && ctx.location !== "未知" && (
                            <span className="text-xs text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded">
                              📍 {ctx.location}
                            </span>
                          )}
                        </div>
                        "{ctx.snippet}"
                      </div>
                    ))}
                    {(!selectedRelation.contexts || selectedRelation.contexts.length === 0) && (
                      <div className="text-sm text-gray-300 bg-gray-800/50 p-3 rounded-lg border border-gray-700/50">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`w-2 h-2 rounded-full ${
                            selectedRelation.sentiment === 'positive' ? 'bg-green-500' :
                            selectedRelation.sentiment === 'negative' ? 'bg-red-500' : 'bg-gray-400'
                          }`}></span>
                        </div>
                        "{selectedRelation.snippet}"
                      </div>
                    )}
                  </div>
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
              className="glass-panel rounded-3xl p-6"
            >
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-100 font-serif-sc">
                <Zap className="w-5 h-5 text-yellow-400" /> 核心枢纽人物 (Top 8)
              </h2>
              <div className="space-y-4">
                {topCharacters.map(([name, deg]: any, idx) => (
                  <div key={name} className="flex items-center justify-between group">
                    <div className="flex items-center gap-3">
                      <span className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${idx < 3 ? 'bg-cyan-500/20 text-cyan-400 neon-border-cyan' : 'bg-gray-800/50 text-gray-400 border border-gray-700'}`}>
                        {idx + 1}
                      </span>
                      <span className={`font-medium ${name === network_analysis.main_character ? 'text-cyan-400 font-bold' : 'text-gray-300'}`}>
                        {name} {name === network_analysis.main_character && '👑'}
                      </span>
                    </div>
                    <div className="text-sm font-mono-code text-gray-500 bg-gray-950/50 px-2 py-1 rounded">
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
              className="glass-panel rounded-3xl p-6"
            >
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-100 font-serif-sc">
                <Award className="w-5 h-5 text-purple-400" /> 命运脉络推演
              </h2>
              <div className="space-y-4 overflow-y-auto max-h-[300px] pr-2 custom-scrollbar">
                {Object.entries(destiny_predictions).slice(0, 4).map(([name, pred]: any) => {
                  const outlook = pred.overall_outlook;
                  const colorClass = outlook === 'positive' ? 'text-green-400 border-green-500/30 bg-green-500/10 neon-border-cyan' : 
                                    outlook === 'negative' ? 'text-red-400 border-red-500/30 bg-red-500/10 shadow-[0_0_15px_rgba(239,68,68,0.15)]' : 
                                    'text-yellow-400 border-yellow-500/30 bg-yellow-500/10 shadow-[0_0_15px_rgba(234,179,8,0.15)]';
                  return (
                    <div key={name} className={`p-4 rounded-2xl border backdrop-blur-md ${colorClass}`}>
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
              className="glass-panel rounded-3xl p-6 flex flex-col h-[400px]"
            >
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-100 font-serif-sc">
                <MessageSquare className="w-5 h-5 text-blue-400" /> 原著知识库问答
              </h2>
              
              <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 custom-scrollbar">
                {chatHistory.length === 0 ? (
                  <div className="text-sm text-gray-500 text-center mt-10">
                    尝试提问：“楚子航为什么要爆血？”
                  </div>
                ) : (
                  chatHistory.map((msg, i) => (
                    <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-cyan-600/80 text-white rounded-br-none neon-border-cyan' : 'glass-panel text-gray-200 rounded-bl-none border-gray-700/50'}`}>
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
                  className="w-full bg-black/40 border border-gray-700 rounded-xl py-3 pl-4 pr-12 text-sm focus:outline-none focus:neon-border-cyan text-white transition-all"
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

      {/* Sandbox Overlay */}
      <AnimatePresence>
        {isSandboxOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xl flex items-center justify-center p-8"
          >
            <div className="w-full max-w-6xl h-full glass-panel neon-border-purple rounded-3xl flex overflow-hidden">
              {/* Left Panel: Config */}
              <div className="w-1/3 bg-gray-900/30 border-r border-gray-800 p-6 flex flex-col">
                <div className="flex justify-between items-center mb-8">
                  <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400 font-serif-sc">
                    平行世界沙盘
                  </h2>
                  <button onClick={() => setIsSandboxOpen(false)} className="text-gray-400 hover:text-white">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  </button>
                </div>
                
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-purple-300 mb-2">1. 选择登场角色 (至少2个)</label>
                    <div className="flex flex-wrap gap-2">
                      {topCharacters.map(([name]: any) => (
                        <button
                          key={name}
                          onClick={() => {
                            if (sandboxCharacters.includes(name)) {
                              setSandboxCharacters(sandboxCharacters.filter(c => c !== name));
                            } else {
                              setSandboxCharacters([...sandboxCharacters, name]);
                            }
                          }}
                          className={`px-3 py-1 rounded-full text-sm transition-all ${
                            sandboxCharacters.includes(name) 
                            ? 'bg-purple-600/80 text-white neon-border-purple' 
                            : 'bg-black/40 text-gray-400 border border-gray-700 hover:neon-border-purple'
                          }`}
                        >
                          {name}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-cyan-300 mb-2">2. 注入蝴蝶效应 (假设变量)</label>
                    <textarea
                      value={sandboxWhatIf}
                      onChange={(e) => setSandboxWhatIf(e.target.value)}
                      placeholder="例如：如果楚子航没有爆血，而是选择向卡塞尔学院求援会怎样？"
                      className="w-full bg-black/40 border border-gray-700 rounded-xl p-4 text-white placeholder-gray-500 focus:outline-none focus:neon-border-cyan h-32 resize-none transition-all"
                    />
                  </div>
                </div>
                
                <button
                  onClick={handleRunSimulation}
                  disabled={isSimulating || sandboxCharacters.length < 2 || !sandboxWhatIf}
                  className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all mt-4 ${
                    isSimulating || sandboxCharacters.length < 2 || !sandboxWhatIf
                    ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-600/80 to-cyan-600/80 hover:from-purple-500 hover:to-cyan-500 text-white neon-border-purple backdrop-blur-md'
                  }`}
                >
                  {isSimulating ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                      正在沙盘中推演...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                      启动深度记忆流推演
                    </>
                  )}
                </button>
              </div>
              
              {/* Right Panel: Result */}
              <div className="flex-1 bg-transparent p-8 flex flex-col relative">
                {!sandboxResult && !isSimulating ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
                    <svg className="w-24 h-24 mb-4 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                    <p className="text-xl font-medium">配置左侧参数，开始创造平行世界</p>
                    <p className="text-sm mt-2">基于 {topCharacters.length} 名角色的性格与数十万字记忆图谱进行推演</p>
                  </div>
                ) : isSimulating ? (
                  <div className="flex-1 flex flex-col items-center justify-center">
                    <div className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin mb-6"></div>
                    <h3 className="text-2xl font-bold text-white mb-2 animate-pulse">正在唤醒角色 Agent...</h3>
                    <p className="text-cyan-400 font-mono text-sm">Loading Context from GraphRAG...</p>
                  </div>
                ) : (
                  <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 flex flex-col gap-6">
                    <div className="glass-panel neon-border-purple rounded-xl p-6">
                      <h3 className="text-purple-400 text-sm font-bold uppercase tracking-wider mb-2 font-serif-sc">上帝视角总结 (Director's Summary)</h3>
                      <p className="text-gray-200 leading-relaxed text-lg">{sandboxResult.summary}</p>
                    </div>
                    
                    <div className="space-y-6 relative">
                      {/* 连接对话的时间线 */}
                      <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-gradient-to-b from-purple-500/50 to-cyan-500/50"></div>
                      
                      {sandboxResult.script.map((msg: any, i: number) => (
                        <motion.div 
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.3 }}
                          key={i} 
                          className="flex gap-4 relative z-10"
                        >
                          <div className="w-12 h-12 rounded-full bg-gray-900 flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(6,182,212,0.3)] flex-shrink-0 border-2 border-cyan-500 z-10 relative mt-2">
                            {msg.character[0]}
                            {/* 顺序序号角标 */}
                            <div className="absolute -bottom-2 -right-2 bg-purple-600 text-[10px] w-5 h-5 rounded-full flex items-center justify-center border border-gray-900">
                              {i + 1}
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-baseline gap-2 mb-1">
                              <span className="font-bold text-cyan-400 text-lg font-serif-sc">{msg.character}</span>
                              {msg.action && <span className="text-sm text-purple-400 italic bg-purple-900/30 px-2 py-0.5 rounded-full border border-purple-500/20">({msg.action})</span>}
                            </div>
                            <div className="glass-panel border border-gray-700/50 hover:neon-border-cyan transition-colors rounded-2xl rounded-tl-none p-5 text-gray-200 leading-relaxed shadow-lg text-lg relative">
                              {/* 气泡小尾巴 */}
                              <div className="absolute -left-2 top-4 w-4 h-4 glass-panel border-l border-t border-gray-700/50 transform -rotate-45"></div>
                              {msg.content}
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}