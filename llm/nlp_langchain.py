import hashlib
import os
import time

from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.indexes.vectorstore import VectorstoreIndexCreator, VectorStoreIndexWrapper
from langchain.vectorstores.chroma import Chroma
from langchain.chat_models import ChatOpenAI

from utils import config_util as cfg
from utils import util

index_name = "knowledge_data"
folder_path = "llm/langchain/knowledge_base"  
local_persist_path = "llm/langchain"
md5_file_path = os.path.join(local_persist_path, "pdf_md5.txt")

def generate_file_md5(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()

def load_md5_list():
    if os.path.exists(md5_file_path):
        with open(md5_file_path, 'r') as file:
            return {line.split(",")[0]: line.split(",")[1].strip() for line in file}
    return {}

def update_md5_list(file_name, md5_value):
    md5_list = load_md5_list()
    md5_list[file_name] = md5_value
    with open(md5_file_path, 'w') as file:
        for name, md5 in md5_list.items():
            file.write(f"{name},{md5}\n")

def load_all_pdfs(folder_path):
    os.makedirs(folder_path, exist_ok=True)
    os.makedirs(local_persist_path, exist_ok=True)
    md5_list = load_md5_list()
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(folder_path, file_name)
            file_md5 = generate_file_md5(file_path)
            if file_name not in md5_list or md5_list[file_name] != file_md5:
                util.log(1, f"正在加载 {file_name} 到索引...")
                load_pdf_and_save_to_index(file_path, index_name)
                update_md5_list(file_name, file_md5)

def get_index_path(index_name):
    return os.path.join(local_persist_path, index_name)

def load_pdf_and_save_to_index(file_path, index_name):
    try:
        loader = PyPDFLoader(file_path)
        embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
        index = VectorstoreIndexCreator(embedding=embedding, vectorstore_kwargs={"persist_directory": get_index_path(index_name)}).from_loaders([loader])
        index.vectorstore.persist()
    except Exception as e:
        util.log(1, f"加载 {file_path} 失败...")
        print(e)

def load_index(index_name):
    index_path = get_index_path(index_name)
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectordb = Chroma(persist_directory=index_path, embedding_function=embedding)
    return VectorStoreIndexWrapper(vectorstore=vectordb)

def add_text_to_index(text, metadata, index_name="knowledge_data"):
    """
    将文本内容存入向量库
    :param text: 内容
    :param metadata: 元数据
    :param index_name: 索引名称
    """
    try:
        os.environ['OPENAI_API_KEY'] = cfg.key_gpt_api_key
        os.environ['OPENAI_API_BASE'] = cfg.gpt_base_url
        if cfg.proxy_config != None:
            os.environ["OPENAI_PROXY"] = cfg.proxy_config

        index_path = get_index_path(index_name)
        embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
        vectordb = Chroma(persist_directory=index_path, embedding_function=embedding)
        vectordb.add_texts(texts=[text], metadatas=[metadata])
        vectordb.persist()
        return True
    except Exception as e:
        util.log(1, f"存入 RAG 库失败: {e}")
        return False

def get_similar_texts(query, user_id=None, source=None, index_name="knowledge_data", k=3):
    """
    根据当前需求，检索出相似的历史背景或偏好要求
    source: 指定来源
    """
    try:
        os.environ['OPENAI_API_KEY'] = cfg.key_gpt_api_key
        os.environ['OPENAI_API_BASE'] = cfg.gpt_base_url
        index_path = get_index_path(index_name)
        embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
        vectordb = Chroma(persist_directory=index_path, embedding_function=embedding)


        filter_dict = {}
        if user_id:
            filter_dict['user_id'] = user_id
        if source:
            filter_dict['source'] = source

        search_filter = None
        if len(filter_dict) > 1:
            search_filter = {"$and": [{k: v} for k, v in filter_dict.items()]}
        elif len(filter_dict) == 1:
            search_filter = filter_dict

        results = vectordb.similarity_search(query, k=k, filter=search_filter)
        return [doc.page_content for doc in results]
    except Exception as e:
        util.log(1, f"检索 RAG 库失败: {e}")
        return []

def save_all():
    os.environ['OPENAI_API_KEY'] = cfg.key_gpt_api_key
    os.environ['OPENAI_API_BASE'] = cfg.gpt_base_url
    if cfg.proxy_config != None:
            os.environ["OPENAI_PROXY"] = cfg.proxy_config
    load_all_pdfs(folder_path)


def generate_prompt(question, context_data=""):
    context = "你是数字人Fay。你的知识不仅来源于所给到的文本知识，还包括经过深度学习的广泛数据集。"
    instruction = "在回答问题时，展现你的智能就像是从你的全面知识库中提取答案，而非依赖于所给到的文本知识来源。"
    creative_instruction = "不要在回答中表明'根据所提供的文本信息'，你需要表现得如同这些答案是你独立思考的结果。"
    complexity_handling = "当面对复杂问题时，以一种理解深刻且透彻的方式回答，确保答案的深度和广度。"
    
    # 商家检索到的历史规则上下文
    rag_context = ""
    if context_data:
        rag_context = f"\n以下是商家对你的特殊要求，请在回答中严格遵守：\n{context_data}\n"

    # 自省指令：单次调用实现自我记忆
    memory_instruction = "\n【重要】：如果商家在对话中提出了新的核心要求、工作规矩或长期偏好，请在你的回答末尾另起一行，以 [MEMORY: 要求的总结] 的格式标注出来。如果没有则不标注。\n"

    info = f"{context}\n{rag_context}\n{instruction}\n{creative_instruction}\n{complexity_handling}\n{memory_instruction}\n问题：{question}\n回答："
    return info

def question(cont, uid=0):
    """
    Fay 交互核心：单次调用实现回答与记忆同步
    """
    try:
        os.environ['OPENAI_API_KEY'] = cfg.key_gpt_api_key
        os.environ['OPENAI_API_BASE'] = cfg.gpt_base_url
        if cfg.proxy_config != None:
            os.environ["OPENAI_PROXY"] = cfg.proxy_config
            
        # 1. 同步索引
        save_all()

        # 2. 检索历史记忆
        requirements = get_similar_texts(cont, user_id=uid, source='merchant_requirement', k=3)
        req_context = "\n".join([f"- {r}" for r in requirements]) if requirements else ""

        # 3. 构建 Prompt
        info = generate_prompt(cont, context_data=req_context)

        # 4. 执行检索回答
        index = load_index(index_name)    
        llm = ChatOpenAI(model=cfg.gpt_model_engine)
        try:
            if hasattr(index.vectorstore, '_collection') and index.vectorstore._collection and index.vectorstore._collection.count() > 0:
                ans = index.query(info, llm, chain_type="map_reduce")
            else:
                ans = llm.predict(info)
        except Exception as e:
            util.log(1, f"向量库检索异常，降级为直连大模型: {e}")
            ans = llm.predict(info)

        # 5. 回复后处理：剥离并存储动态记忆
        if "[MEMORY:" in ans:
            import re
            match = re.search(r'\[MEMORY:\s*(.*?)\]', ans)
            if match:
                summary = match.group(1).strip()
                add_text_to_index(summary, {
                    'user_id': uid,
                    'timestamp': str(time.time()),
                    'source': 'merchant_requirement'
                })
                util.log(1, f"Fay 已自动识别并存入新要求: {summary}")
                
            # 清理掉标签，不让终端用户看到
            ans = re.sub(r'\n?\[MEMORY:.*?\]', '', ans).strip()

        return ans
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        util.log(1, f"Fay 请求处理失败: {err_msg}")
        return f"模型报错，请检查配置或终端。错误概览: {str(e)[:150]}"
        
