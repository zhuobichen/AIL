import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Book, Zap, ArrowRight, Activity } from 'lucide-react';
import { uploadTask } from '@/api/client';
import { motion } from 'framer-motion';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [book, setBook] = useState('longzu');
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!file) return;
    setIsUploading(true);
    try {
      const data = await uploadTask(file, book);
      navigate(`/task/${data.task_id}`);
    } catch (error) {
      console.error(error);
      alert('上传失败，请检查后端是否启动。');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gray-950">
      {/* Background decoration */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-cyan-900/20 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-fuchsia-900/20 blur-[120px] rounded-full" />
        <div className="absolute top-[40%] left-[50%] translate-x-[-50%] w-[80%] h-[20%] bg-indigo-900/10 blur-[100px] rounded-full" />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-10 w-full max-w-3xl p-8"
      >
        <div className="text-center mb-12">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="inline-flex items-center justify-center p-3 mb-6 rounded-2xl bg-gray-900/50 border border-gray-800 shadow-xl backdrop-blur-xl"
          >
            <Activity className="w-8 h-8 text-cyan-400" />
          </motion.div>
          <h1 className="text-5xl md:text-6xl font-black mb-6 tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-white via-gray-200 to-gray-500">
            数字人文叙事 <span className="text-cyan-400">AI</span>
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto font-light">
            基于大语言模型的长篇小说结构化解析引擎。上传你的纯文本文件，我们将为你重构隐藏在文字背后的深层社交图谱与命运脉络。
          </p>
        </div>

        <div className="bg-gray-900/40 backdrop-blur-2xl border border-gray-800/50 rounded-3xl p-8 shadow-2xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            
            {/* File Upload Zone */}
            <div className="space-y-4">
              <label className="text-sm font-medium text-gray-400 flex items-center gap-2">
                <Upload className="w-4 h-4" /> 上传小说文本 (.txt)
              </label>
              <div 
                className={`relative group flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-2xl transition-all duration-300 ease-in-out cursor-pointer overflow-hidden
                  ${dragActive ? 'border-cyan-500 bg-cyan-950/20' : 'border-gray-800 hover:border-gray-600 bg-gray-950/50'}
                  ${file ? 'border-green-500/50 bg-green-950/10' : ''}
                `}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input 
                  ref={fileInputRef}
                  type="file" 
                  accept=".txt" 
                  onChange={handleChange} 
                  className="hidden" 
                />
                
                {file ? (
                  <motion.div 
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="flex flex-col items-center text-center p-4"
                  >
                    <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center mb-3 text-green-400">
                      <Book className="w-6 h-6" />
                    </div>
                    <p className="text-gray-200 font-medium truncate max-w-[200px]">{file.name}</p>
                    <p className="text-xs text-gray-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </motion.div>
                ) : (
                  <div className="flex flex-col items-center text-center p-4">
                    <div className="w-12 h-12 rounded-full bg-gray-800 group-hover:bg-gray-700 flex items-center justify-center mb-3 text-gray-400 transition-colors">
                      <Upload className="w-6 h-6" />
                    </div>
                    <p className="text-gray-300 font-medium">点击或拖拽文件至此</p>
                    <p className="text-xs text-gray-500 mt-2">仅支持 UTF-8 编码的 .txt 文件</p>
                  </div>
                )}
              </div>
            </div>

            {/* Config Zone */}
            <div className="space-y-6 flex flex-col justify-between">
              <div className="space-y-4">
                <label className="text-sm font-medium text-gray-400 flex items-center gap-2">
                  <Book className="w-4 h-4" /> 预设人物知识库
                </label>
                <div className="relative">
                  <select 
                    value={book} 
                    onChange={(e) => setBook(e.target.value)}
                    className="w-full bg-gray-950/50 border border-gray-800 text-gray-200 rounded-xl px-4 py-3 appearance-none focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all"
                  >
                    <option value="longzu">《龙族》全集 (江南)</option>
                    <option value="hongloumeng">《红楼梦》 (曹雪芹)</option>
                    <option value="sanguo">《三国演义》 (罗贯中)</option>
                    <option value="xiyouji">《西游记》 (吴承恩)</option>
                    <option value="default">自动推断 (通用)</option>
                  </select>
                  <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-gray-500">
                    <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" /></svg>
                  </div>
                </div>
                <p className="text-xs text-gray-500">选择正确的预设词典可以大幅提升人物名称识别的准确率与别名解析的稳定性。</p>
              </div>

              <button 
                onClick={handleSubmit}
                disabled={!file || isUploading}
                className={`group relative w-full flex items-center justify-center gap-2 py-4 rounded-xl font-medium transition-all overflow-hidden
                  ${!file ? 'bg-gray-800 text-gray-500 cursor-not-allowed' : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_20px_rgba(8,145,178,0.4)] hover:shadow-[0_0_30px_rgba(8,145,178,0.6)]'}
                `}
              >
                {isUploading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    初始化中...
                  </span>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    开始深度解析
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>

          </div>
        </div>
      </motion.div>
    </div>
  );
}