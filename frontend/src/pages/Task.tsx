import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTaskStatus } from '@/api/client';
import { Loader2, CheckCircle, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Task() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    if (!taskId) return;
    
    let interval = setInterval(async () => {
      try {
        const data = await getTaskStatus(taskId);
        setStatus(data);
        
        if (data.status === 'completed') {
          clearInterval(interval);
          setTimeout(() => {
            navigate(`/report/${taskId}`);
          }, 1000);
        } else if (data.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error(err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId, navigate]);

  if (!status) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-950 p-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-cyan-900/10 blur-[150px] rounded-full pointer-events-none" />

      <motion.div 
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-xl bg-gray-900/60 backdrop-blur-xl border border-gray-800 rounded-3xl p-10 shadow-2xl z-10"
      >
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-4 mb-6 rounded-full bg-gray-800/50 border border-gray-700">
            {status.status === 'failed' ? (
              <AlertTriangle className="w-10 h-10 text-red-500" />
            ) : status.status === 'completed' ? (
              <CheckCircle className="w-10 h-10 text-green-500" />
            ) : (
              <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
            )}
          </div>
          <h2 className="text-3xl font-bold text-gray-100 mb-2">
            {status.status === 'pending' && '排队中'}
            {status.status === 'processing' && 'AI 正在深度阅读...'}
            {status.status === 'completed' && '解析完成！'}
            {status.status === 'failed' && '解析失败'}
          </h2>
          <p className="text-gray-400">正在分析书籍: <span className="text-cyan-400">{status.book_name}</span></p>
        </div>

        <div className="space-y-4">
          <div className="flex justify-between text-sm font-medium text-gray-400 mb-2">
            <span>分析进度</span>
            <span>{status.progress.toFixed(1)}%</span>
          </div>
          
          <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
            <motion.div 
              className={`h-full rounded-full ${status.status === 'failed' ? 'bg-red-500' : 'bg-gradient-to-r from-cyan-600 to-cyan-400'}`}
              initial={{ width: 0 }}
              animate={{ width: `${status.progress}%` }}
              transition={{ ease: "easeOut", duration: 0.5 }}
            />
          </div>

          <div className="mt-6 p-4 bg-gray-950/50 border border-gray-800 rounded-xl font-mono text-sm text-gray-300">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
              <span className="text-cyan-500">System Log</span>
            </div>
            {status.message}
          </div>
        </div>
      </motion.div>
    </div>
  );
}