import os
import chromadb
from chromadb.utils import embedding_functions

# 使用国内可直连的模型，避免 huggingface.co 连不上
# 这里改用轻量级无依赖的内置模型，自动从默认地址下载或使用缓存
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

class RAGKnowledgeBase:
    def __init__(self, db_path=".llm_cache/chroma_db", collection_name="narrative_texts"):
        self.db_path = db_path
        self.collection_name = collection_name
        
        # 确保目录存在
        os.makedirs(db_path, exist_ok=True)
        
        # 初始化 ChromaDB 客户端 (持久化存储)
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 尝试设置 HuggingFace 镜像代理以防止网络超时
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        
        # 初始化嵌入函数
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        
        # 获取或创建 Collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"} # 使用余弦相似度
        )

    def add_texts(self, chunks: list[str], book_name: str):
        """
        将文本块添加到向量数据库
        """
        if not chunks:
            return
            
        ids = [f"{book_name}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"book": book_name, "chunk_index": i} for i in range(len(chunks))]
        
        # 为了避免重复添加，先检查已有的 ID
        existing_ids = set(self.collection.get(ids=ids)["ids"])
        
        new_chunks = []
        new_ids = []
        new_metadatas = []
        
        for i, chunk_id in enumerate(ids):
            if chunk_id not in existing_ids:
                new_chunks.append(chunks[i])
                new_ids.append(chunk_id)
                new_metadatas.append(metadatas[i])
                
        if new_chunks:
            # 批量添加到 ChromaDB
            self.collection.add(
                documents=new_chunks,
                ids=new_ids,
                metadatas=new_metadatas
            )
            print(f"成功将 {len(new_chunks)} 个新文本块添加到向量库。")
        else:
            print("所有文本块已存在于向量库中，跳过添加。")

    def search(self, query: str, book_name: str = None, top_k: int = 5) -> list[dict]:
        """
        基于语义搜索最相关的文本片段
        """
        where_filter = {"book": book_name} if book_name else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )
        
        if not results['documents'] or not results['documents'][0]:
            return []
            
        snippets = []
        for i, doc in enumerate(results['documents'][0]):
            snippets.append({
                "text": doc,
                "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else 0,
                "metadata": results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {}
            })
            
        return snippets
