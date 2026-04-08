import os
import sys
from dotenv import load_dotenv
from flask import redirect, url_for
import numpy as np
import pandas as pd
from datetime import datetime
from flask_caching import Cache
from collections import defaultdict

# 加载 .env 文件
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
load_dotenv(os.path.join(project_root, '.env'), override=True)


# 将项目根目录添加到 sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 现在可以安全地导入项目模块了 ---

# 导入配置工具
from utils import config_util

#  导入标准库和第三方库 ---
from flask import (
    Flask,
    request,
    jsonify,
    send_file,
    send_from_directory,
    redirect,
    url_for,
    Response,
    stream_with_context,
    session,
    make_response,
    after_this_request,
)
from flask_cors import CORS
from gevent import pywsgi  #提升文件加载的流畅度，防止“排队等待” ，不然live2d可以是一个头一个脚加载出来
from tts import tts_voice
from tts import qwen3
from tts import volcano_tts
from scheduler.thread_manager import MyThread
from core import wsa_server
from core.task_db import Task_Db
import subprocess
from http import HTTPStatus
from urllib.parse import urlparse, unquote, urlencode
from pathlib import PurePosixPath, Path
import requests
from dashscope import ImageSynthesis
from werkzeug.exceptions import HTTPException
import hmac
import base64
import uuid   #随机生成库
import time
import hashlib
import json
import traceback
from threading import Lock, Thread
from datetime import datetime
import oss2
import redis
from gui.platforms import PLATFORM_CONFIG, COST_CONFIG
from gui.ai_tools_task_result_utils import (
    build_image_task_result,
    build_video_task_result,
    extract_task_product_id,
    merge_saved_video_result,
)
from backend.services.live_service import live_service

#初始化Flask并配置一些基本设置
app = Flask(__name__, static_url_path='/static')  #指定静态文件的URL路径为/static,图片等的路径
app.secret_key=str(uuid.uuid4())  # 生成随机密钥
app.config['TEMPLATES_AUTO_RELOAD'] = True  # 开启模板自动重载，，下一次请求时就会自动加载最新的模板内容，方便调试
app.debug = True  #本地自动调试


#全局异常处理器
@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    print(traceback.format_exc())
    return jsonify({"status": "error", "error": str(e)}), 500

CORS(app)

# 配置缓存
cache_config = {
    'CACHE_TYPE': 'redis',  # 使用Redis作为缓存后端
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300,  # 默认5分钟
    'CACHE_KEY_PREFIX': 'dashboard_'
}
cache = Cache(config=cache_config)
cache.init_app(app)
# =============================================================================
# LiblibAI 平台配置
# 配置来源：从 .env 环境变量文件读取
# 配置项说明：
#   LIBLIB_ACCESS_KEY - LiblibAI 平台的 Access Key
#   LIBLIB_SECRET_KEY - LiblibAI 平台的 Secret Key
#   LIBLIB_API_BASE   - LiblibAI API 基础地址
# 获取方式：请在 https://liblibai.cloud/ 平台注册并获取 API 密钥
# =============================================================================
def get_liblib_config():
    """
    获取 LiblibAI 平台配置
    从环境变量读取配置，如果缺失则抛出异常并提示用户
    """
    config = {
        'ACCESS_KEY': os.getenv('LIBLIB_ACCESS_KEY'),
        'SECRET_KEY': os.getenv('LIBLIB_SECRET_KEY'),
        'API_BASE': os.getenv('LIBLIB_API_BASE', 'https://openapi.liblibai.cloud')
    }
    
    # 验证必要配置是否存在
    missing_keys = []
    if not config['ACCESS_KEY']:
        missing_keys.append('LIBLIB_ACCESS_KEY')
    if not config['SECRET_KEY']:
        missing_keys.append('LIBLIB_SECRET_KEY')
    
    if missing_keys:
        error_msg = f"""
[错误] LiblibAI 平台配置缺失！

缺少以下环境变量：
{chr(10).join(['  - ' + key for key in missing_keys])}

请在项目根目录的 .env 文件中添加以下配置：
LIBLIB_ACCESS_KEY=你的AccessKey
LIBLIB_SECRET_KEY=你的SecretKey
LIBLIB_API_BASE=https://openapi.liblibai.cloud

获取方式：
1. 访问 https://liblibai.cloud/
2. 登录后进入个人中心
3. 在 API 管理页面获取密钥
        """
        print(error_msg)
        raise ValueError(error_msg)
    
    return config

# 初始化 LiblibAI 配置（启动时验证）
try:
    LIBLIB_CONFIG = get_liblib_config()
    print(f"[LiblibAI] 配置加载成功，API地址: {LIBLIB_CONFIG['API_BASE']}")
except ValueError as e:
    LIBLIB_CONFIG = None
    print(f"[LiblibAI] 配置加载失败: {e}")

# 视频生成配置
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# 注意：视频生成使用的密钥已从环境变量读取，不再使用硬编码

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制上传文件大小，阻止超大文件上传
#大小设置
# 创建上传目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- Dashboard Redirects -----------------

@app.route('/home')
def home():
    return render_template('index_main.html')

@app.route('/dashboard')
def dashboard_redirect():
    return redirect("http://localhost:5001/dashboard")

@app.route('/dashboard.html')
def dashboard_html_redirect():
    return redirect("http://localhost:5001/dashboard.html")

@app.route('/dashboard_internal')
def dashboard_internal_redirect():
    return _legacy_page_retired("dashboard_internal", "/dashboard/analytics/analyst")

@app.route('/dashboard_internal.html')
def dashboard_internal_html_redirect():
    return redirect("http://localhost:5001/dashboard_internal.html")

# ----------------- Dashboard Logic End -----------------



@app.route('/favicon.ico')
def favicon():
    try:
        static_images_dir = os.path.join(app.static_folder, 'images')
        static_ico = os.path.join(static_images_dir, 'favicon.ico')  #拼接路径，得到完整的图标路径（例/path/to/project/static/images/favicon.ico）
        if os.path.exists(static_ico):#先在image目录下找favicon.ico路径
            return send_from_directory(static_images_dir, 'favicon.ico', mimetype='image/x-icon')
        root_dir = os.path.dirname(app.root_path)
        root_ico = os.path.join(root_dir, 'favicon.ico')
        if os.path.exists(root_ico):#在根目录下找favicon.ico路径
            return send_from_directory(root_dir, 'favicon.ico', mimetype='image/x-icon')
        return redirect(url_for('static', filename='images/kode-icon.png'))
    #如果两个位置都没找到，返回默认图标
    except Exception:
        return redirect(url_for('static', filename='images/kode-icon.png'))
    #如果发生报错，也重定向到默认图标，避免图标加载不出这种情况




@app.route('/customer_analysis')
def customer_analysis():
    return render_template('customer_analysis.html')

@app.route('/api/analyze_customer', methods=['POST'])
def analyze_customer():
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        customer_data = data.get('customer_data')
        marketing_goal = data.get('marketing_goal')

        # 构建 Prompt
        # 这里我们利用 DashScope (通义千问) 或 OpenAI 接口
        # 为了演示，如果没配置key，我们返回模拟数据
        
        prompt = f"""
        你是一位专业的消费心理学家和金牌电商文案。
        
        【任务 1：客户画像分析】
        请根据以下客户数据，分析该客户的：
        1. 核心需求（Need）
        2. 痛点/担忧（Pain Point）
        3. 消费能力与偏好（Buying Power）
        4. 心理关键词（3-5个标签）
        
        客户数据：
        "{customer_data}"
        
        【任务 2：精准营销话术生成】
        商品：{product_name}
        营销目标：{marketing_goal} (conversion=转化, trust=信任, recall=召回)
        
        请针对上述分析出的客户画像，写一段直击人心的营销话术。
        要求：
        - 不要用通用的广告语，要针对他/她的具体痛点。
        - 语气风格要符合营销目标。
        - 300字以内。
        
        【输出格式】
        请直接返回 JSON 格式字符串，不要包含 Markdown 代码块：
        {{
            "analysis": "这里是 markdown 格式的客户画像分析...",
            "copy": "这里是生成的营销话术..."
        }}
        """

        # 尝试调用大模型 (这里优先尝试 DashScope，如果失败则返回模拟数据)
        try:
            import dashscope
            # 检查是否有 API KEY，如果没有则使用模拟数据
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if not api_key:
                 raise Exception("No API Key configured")

            response = dashscope.Generation.call(
                model=dashscope.Generation.Models.qwen_turbo,
                prompt=prompt,
                api_key=api_key
            )
            
            if response.status_code == HTTPStatus.OK:
                content = response.output.text
                # 尝试解析 JSON
                # 有时候模型会包裹在 ```json ... ``` 中
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group(0))
                    return jsonify({'status': 'success', 'analysis': result['analysis'], 'copy': result['copy']})
                else:
                    # 如果解析失败，直接返回全文
                    return jsonify({'status': 'success', 'analysis': content, 'copy': "解析格式失败，请查看分析结果"})
            else:
                 raise Exception(f"API Error: {response.message}")

        except Exception as e:
            print(f"LLM调用失败，使用模拟/规则兜底: {e}")
            # 模拟返回 (当没有 API Key 时展示效果)
            mock_analysis = f"""
            **核心需求**：用户对{product_name}有明确兴趣，但存在疑虑。
            **痛点**：{customer_data[:20]}... (基于输入推测)
            **标签**：`价格敏感` `追求性价比` `需建立信任`
            """
            mock_copy = f"""
            👋 亲，看到您对{product_name}很感兴趣！
            
            针对您担心的...问题，我们这款产品特别采用了...
            
            🔥 现在下单还有限时优惠，支持7天无理由退换，试错成本我们承担！
            """
            return jsonify({'status': 'success', 'analysis': mock_analysis, 'copy': mock_copy})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500



@app.route('/submit-form-data', methods=['POST'])
def submit_form_data():
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        ad_best = data.get('ad_best')
        copy_type = data.get('copy_type', 'marketing')
        
        if not product_name or not ad_best:
            return jsonify({'status': 'error', 'message': '缺少商品名称或文案内容'}), 400
            
        # 初始化OSS客户端
        auth = oss2.Auth(OSS_CONFIG['ACCESS_KEY_ID'], OSS_CONFIG['ACCESS_KEY_SECRET'])
        bucket = oss2.Bucket(auth, OSS_CONFIG['ENDPOINT'], OSS_CONFIG['BUCKET_NAME'])
        
        # 查找商品ID
        target_product_id = None
        prefix = 'products/'
        
        # 遍历所有商品查找匹配的名称
        for obj in oss2.ObjectIterator(bucket, prefix=prefix, delimiter='/'):
            if obj.is_prefix() and obj.key.count('/') == 2:
                prod_id = obj.key.split('/')[1]
                if not prod_id.startswith('prod_'):
                    continue
                    
                info_path = f'{prefix}{prod_id}/info.json'
                try:
                    if bucket.object_exists(info_path):
                        info_content = bucket.get_object(info_path).read()
                        info = json.loads(info_content)
                        if info.get('name') == product_name:
                            target_product_id = prod_id
                            break
                except Exception:
                    continue
        
        if not target_product_id:
             return jsonify({'status': 'error', 'message': '未在商品库中找到该商品，请先在"商品基础信息库"中添加商品'}), 404
             
        # 保存营销文案
        # 这里为了兼容 product_marketing.html，我们统一保存到 marketing.txt
        # 如果需要区分类型，可以考虑追加或者使用不同文件名，但目前前端只读 marketing.txt
        text_path = f'products/{target_product_id}/generated_content/marketing.txt'
        
        # 如果是追加模式 (可选)
        # current_content = ""
        # if bucket.object_exists(text_path):
        #     current_content = bucket.get_object(text_path).read().decode('utf-8') + "\n\n"
        # bucket.put_object(text_path, current_content + f"[{copy_type}] {ad_best}")
        
        # 目前采用覆盖模式，或者如果用户希望是"最佳方案"，那应该是覆盖
        bucket.put_object(text_path, ad_best)
        
        return jsonify({'status': 'success', 'message': '已成功保存到商品营销素材库'})
        
    except Exception as e:
        print(f"Error saving form data: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/delete_marketing_materials', methods=['POST'])
def delete_marketing_materials():
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        
        if not product_name:
            return jsonify({'status': 'error', 'message': '缺少商品名称'}), 400
            
        # 检查OSS配置
        if not OSS_CONFIG.get('ACCESS_KEY_ID') or not OSS_CONFIG.get('ACCESS_KEY_SECRET'):
            print("错误: 未配置阿里云OSS密钥")
            # 这里返回200状态码，但status为error，以便前端能正常处理并显示消息
            # 或者前端需要修改以处理500错误
            return jsonify({'status': 'error', 'message': '未配置OSS密钥，无法执行删除操作'}), 200 

        # 连接OSS
        auth = oss2.Auth(OSS_CONFIG['ACCESS_KEY_ID'], OSS_CONFIG['ACCESS_KEY_SECRET'])
        bucket = oss2.Bucket(auth, OSS_CONFIG['ENDPOINT'], OSS_CONFIG['BUCKET_NAME'])
        
        print(f"开始查找商品: {product_name}")
        
        # 1. 查找商品ID
        # 这里需要遍历 products/ 下的目录，或者如果你有 product_name 到 product_id 的映射
        # 简单起见，我们遍历 products/prod_* 目录下的 info.json
        
        target_product_id = None
        prefix = 'products/'
        
        # 遍历所有商品查找匹配的名称
        # 注意：这在商品数量很多时效率较低，建议建立索引或数据库
        for obj in oss2.ObjectIterator(bucket, prefix=prefix, delimiter='/'):
            if obj.is_prefix() and obj.key.count('/') == 2:
                prod_id = obj.key.split('/')[1]
                if not prod_id.startswith('prod_'):
                    continue
                    
                info_path = f'{prefix}{prod_id}/info.json'
                try:
                    if bucket.object_exists(info_path):
                        info_content = bucket.get_object(info_path).read()
                        info = json.loads(info_content)
                        if info.get('name') == product_name:
                            target_product_id = prod_id
                            break
                except Exception as e:
                    print(f"读取 {info_path} 失败: {e}")
                    continue
        
        if not target_product_id:
            print(f"未找到商品: {product_name}")
            return jsonify({'status': 'error', 'message': f'未找到商品: {product_name}'}), 200 # 返回200让前端处理逻辑错误
            
        print(f"找到商品ID: {target_product_id}，开始删除营销素材...")

        # 2. 删除营销素材
        # 营销素材通常存储在 products/{id}/marketing/ 目录下
        marketing_prefix = f'products/{target_product_id}/marketing/'
        
        deleted_count = 0
        for obj in oss2.ObjectIterator(bucket, prefix=marketing_prefix):
            bucket.delete_object(obj.key)
            deleted_count += 1
            
        print(f"删除完成，共删除 {deleted_count} 个文件")
        
        return jsonify({
            'status': 'success', 
            'message': f'已删除 {deleted_count} 个营销素材文件',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        print(f"删除营销素材失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 200 # 返回200让前端展示具体错误

# chat-------------------------------------------------------------------------------------------
def chat(query):
    api_key = os.getenv('DIFY_WORKFLOW_KEY')
    headers = {
        'Authorization': f'Bearer {api_key}' if api_key else '',
        'Content-Type': 'application/json',
    }
    # 根据小红书文案生成工作流构建请求体
    payload = {
        "inputs": {
            "basic_instruction": query  # 用户输入作为基础指令
        },
        "response_mode": "blocking",
        "user": "user_123"  # 用户标识符
    }
    
    try:
        response = requests.post(
            "https://api.dify.ai/v1/workflows/run",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        response_data = response.json()
        
        # 提取小红书文案和话题
        if response_data.get('status') == 'succeeded':
            outputs = response_data.get('data', {}).get('outputs', {})
            red_content = outputs.get('red_content', '')
            red_hashtag = outputs.get('red_hashtag', '')
            
            # 组合返回结果
            result = f"{red_content}\n\n{red_hashtag}" if red_hashtag else red_content
            return result
        else:
            return "文案生成失败，请稍后再试"
            
    except requests.exceptions.Timeout:
        return "请求超时，请稍后再试"
    except requests.exceptions.RequestException as e:
        print(f"Dify API请求失败: {str(e)}")
        return "文案生成服务暂时不可用"
    except Exception as e:
        print(f"处理响应出错: {str(e)}")
        return "处理文案结果时出错"

# 在chat函数下方添加新的API处理函数
@app.route("/api/chat", methods=["post"])
def api_chat():
    try:
        payload, status = live_service.submit_chat(request.get_json(force=True))
        return jsonify(payload), status
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"/api/chat failed: {exc}"}), 500

@app.route("/api/get-data", methods=["post"])
def api_get_data():
    return jsonify(live_service.get_runtime_payload())


@app.route("/api/submit", methods=["post"])
def api_submit():
    return jsonify(live_service.save_runtime_payload(request))


@app.route("/api/start-live", methods=["post"])
def api_start_live():
    return jsonify(live_service.start_live())


@app.route("/api/stop-live", methods=["post"])
def api_stop_live():
    return jsonify(live_service.stop_live())


@app.route("/api/get-msg", methods=["post"])
def api_get_msg():
    return jsonify(live_service.get_message_history(request))


@app.route("/api/get-member-list", methods=["post"])
def api_get_member_list():
    return jsonify(live_service.get_member_list())


@app.route("/api/asr", methods=["post"])
def api_asr():
    upload = request.files.get("file")
    payload, status = live_service.transcribe_audio(upload)
    return jsonify(payload), status


@app.route("/api/latest-audio", methods=["get"])
def api_latest_audio():
    since_raw = request.args.get("since")
    try:
        since = int(since_raw) if since_raw else None
    except (TypeError, ValueError):
        since = None
    return jsonify(live_service.get_latest_audio(since))


@app.route("/audio/<path:filename>", methods=["get"])
def serve_audio_file(filename):
    return live_service.serve_audio_file(filename)


@app.route('/api/ws-status')
def ws_status():
    return jsonify(live_service.get_ws_status())

@app.route('/v1/chat/completions', methods=['post'])
@app.route('/api/send/v1/chat/completions', methods=['post'])
def api_send_v1_chat_completions():
    try:
        payload = live_service.create_chat_completion(request.get_json(silent=True))
        return jsonify(payload)
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"chat completion failed: {exc}"}), 500

# 获取单个商品详情
@app.route('/get_product/<product_id>')
def get_product(product_id):
    try:
        auth = oss2.Auth(OSS_CONFIG['ACCESS_KEY_ID'], OSS_CONFIG['ACCESS_KEY_SECRET'])
        bucket = oss2.Bucket(auth, OSS_CONFIG['ENDPOINT'], OSS_CONFIG['BUCKET_NAME'])
        
        info_path = f'products/{product_id}/info.json'
        if not bucket.object_exists(info_path):
            return jsonify({'status': 'error', 'error': '商品不存在'}), 404
            
        info = bucket.get_object(info_path).read()
        product = json.loads(info)
        product['id'] = product_id
        
        # 获取所有图片
        image_prefix = f'products/{product_id}/original_images/'
        product['images'] = [
            f"https://{OSS_CONFIG['CUSTOM_DOMAIN']}/{obj.key}"
            for obj in oss2.ObjectIterator(bucket, prefix=image_prefix)
            if not obj.key.endswith('/')
        ]
        
        return jsonify(product)
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# 获取商品详情 (确保端点唯一)
@app.route('/get_product_detail/<product_id>')
def get_product_detail(product_id):
    try:
        auth = oss2.Auth(OSS_CONFIG['ACCESS_KEY_ID'], OSS_CONFIG['ACCESS_KEY_SECRET'])
        bucket = oss2.Bucket(auth, OSS_CONFIG['ENDPOINT'], OSS_CONFIG['BUCKET_NAME'])
        
        info_path = f'products/{product_id}/info.json'
        if not bucket.object_exists(info_path):
            return jsonify({'status': 'error', 'error': '商品不存在'}), 404
            
        info = bucket.get_object(info_path).read()
        product = json.loads(info)
        
        # 获取所有图片
        product['images'] = [
            f"https://{OSS_CONFIG['CUSTOM_DOMAIN']}/{obj.key}"
            for obj in oss2.ObjectIterator(bucket, prefix=f'products/{product_id}/')
            if obj.key.endswith(('.jpg', '.png', '.gif', '.webp'))
        ]
        
        return jsonify({
            'status': 'success',
            'product': product
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# 获取商品营销素材
@app.route('/get_marketing_materials/<product_name>')
def get_marketing_materials(product_name):
    try:
        auth = oss2.Auth(OSS_CONFIG['ACCESS_KEY_ID'], OSS_CONFIG['ACCESS_KEY_SECRET'])
        bucket = oss2.Bucket(auth, OSS_CONFIG['ENDPOINT'], OSS_CONFIG['BUCKET_NAME'])
        
        # 1. 查找商品目录
        product_prefix = f"products/prod_{product_name}_"
        for obj in oss2.ObjectIterator(bucket, prefix=product_prefix, delimiter='/'):
            if obj.is_prefix():
                product_id = obj.key.split('/')[1]
                break
        else:
            return jsonify({'status': 'error', 'error': '商品不存在'}), 404
        
        # 2. 获取营销素材
        marketing_data = {
            'product_name': product_name,
            'copywriting': '',
            'images': [],
            'videos': []
        }
        
        # 读取营销文案
        copy_path = f'products/{product_id}/marketing/copywriting.txt'
        if bucket.object_exists(copy_path):
            marketing_data['copywriting'] = bucket.get_object(copy_path).read().decode('utf-8')
        
        # 获取营销图片
        images_path = f'products/{product_id}/marketing/images/'
        for img in oss2.ObjectIterator(bucket, prefix=images_path):
            if not img.key.endswith('/'):
                marketing_data['images'].append(f"https://{OSS_CONFIG['CUSTOM_DOMAIN']}/{img.key}")
        
        # 获取营销视频
        videos_path = f'products/{product_id}/marketing/videos/'
        for video in oss2.ObjectIterator(bucket, prefix=videos_path):
            if not video.key.endswith('/'):
                marketing_data['videos'].append(f"https://{OSS_CONFIG['CUSTOM_DOMAIN']}/{video.key}")
        
        return jsonify({'status': 'success', 'data': marketing_data})
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/get_all_marketing_products')
def get_all_marketing_products():
    try:
        auth = oss2.Auth(OSS_CONFIG['ACCESS_KEY_ID'], OSS_CONFIG['ACCESS_KEY_SECRET'])
        bucket = oss2.Bucket(auth, OSS_CONFIG['ENDPOINT'], OSS_CONFIG['BUCKET_NAME'])
        
        products = []
        prefix = 'products/'
        
        # 遍历所有商品目录
        for obj in oss2.ObjectIterator(bucket, prefix=prefix, delimiter='/'):
            if obj.is_prefix() and obj.key.startswith('products/prod_') and obj.key.count('/') == 2:
                product_id = obj.key.split('/')[1]
                
                # 获取商品基本信息
                info_path = f'{prefix}{product_id}/info.json'
                if not bucket.object_exists(info_path):
                    continue
                
                try:
                    info = json.loads(bucket.get_object(info_path).read())
                    
                    # 获取营销素材
                    marketing_data = {
                        'product_id': product_id,
                        'product_name': info.get('name', '未命名商品'),
                        'marketing_text': '',
                        'posters': [],
                        'videos': []
                    }
                    
                    # 读取营销文案
                    text_path = f'{prefix}{product_id}/generated_content/marketing.txt'
                    if bucket.object_exists(text_path):
                        marketing_data['marketing_text'] = bucket.get_object(text_path).read().decode('utf-8')
                    
                    # 获取海报图片
                    posters_path = f'{prefix}{product_id}/generated_content/images/'
                    for poster in oss2.ObjectIterator(bucket, prefix=posters_path):
                        if not poster.key.endswith('/'):
                            marketing_data['posters'].append({
                                'url': f"https://{OSS_CONFIG['CUSTOM_DOMAIN']}/{poster.key}",
                                'filename': poster.key.split('/')[-1]
                            })
                    
                    # 获取视频
                    videos_path = f'{prefix}{product_id}/generated_content/videos/'
                    for video in oss2.ObjectIterator(bucket, prefix=videos_path):
                        if not video.key.endswith('/'):
                            marketing_data['videos'].append({
                                'url': f"https://{OSS_CONFIG['CUSTOM_DOMAIN']}/{video.key}",
                                'filename': video.key.split('/')[-1]
                            })
                    
                    products.append(marketing_data)
                except Exception as e:
                    print(f"处理商品 {product_id} 出错: {str(e)}")
                    continue
        
        return jsonify({'status': 'success', 'data': products})
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/delete_marketing/<product_id>', methods=['DELETE'])
def delete_marketing_content(product_id):
    try:
        auth = oss2.Auth(OSS_CONFIG['ACCESS_KEY_ID'], OSS_CONFIG['ACCESS_KEY_SECRET'])
        bucket = oss2.Bucket(auth, OSS_CONFIG['ENDPOINT'], OSS_CONFIG['BUCKET_NAME'])
        
        # 只删除营销内容，保留商品基本信息
        prefix = f'products/{product_id}/generated_content/'
        for obj in oss2.ObjectIterator(bucket, prefix=prefix):
            bucket.delete_object(obj.key)
            
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/oss/products', methods=['GET'])
def get_oss_products():
    try:
        category = request.args.get('category', '')
        has_images = request.args.get('has_images', 'false').lower() == 'true'
        
        auth = oss2.Auth(OSS_CONFIG['ACCESS_KEY_ID'], OSS_CONFIG['ACCESS_KEY_SECRET'])
        bucket = oss2.Bucket(auth, OSS_CONFIG['ENDPOINT'], OSS_CONFIG['BUCKET_NAME'])
        
        products = []
        
        # 方法1：通过分类索引查找
        if category:
            index_path = f'products/_index/by_category/{category}.json'
            if bucket.object_exists(index_path):
                index_data = json.loads(bucket.get_object(index_path).read())
                for item in index_data:
                    info_path = f'products/{item["product_id"]}/info.json'
                    if bucket.object_exists(info_path):
                        info = json.loads(bucket.get_object(info_path).read())
                        # 检查是否有图片的条件
                        if not has_images or (info.get('images') and len(info['images']) > 0):
                            products.append({
                                'id': item['product_id'],
                                'name': info.get('name', '未命名商品'),
                                'images': info.get('images', []),
                                'main_image': item.get('main_image') or 
                                             (info['images'][0] if info.get('images') else None)
                            })
        
        # 方法2：全量扫描（分类为空时）
        else:
            for obj in oss2.ObjectIterator(bucket, prefix='products/', delimiter='/'):
                if obj.is_prefix() and obj.key.startswith('products/prod_') and obj.key.count('/') == 2:
                    product_id = obj.key.split('/')[1]
                    info_path = f'products/{product_id}/info.json'
                    
                    if bucket.object_exists(info_path):
                        info = json.loads(bucket.get_object(info_path).read())
                        # 检查是否有图片的条件
                        if not has_images or (info.get('images') and len(info['images']) > 0):
                            products.append({
                                'id': product_id,
                                'name': info.get('name', '未命名商品'),
                                'images': info.get('images', []),
                                'main_image': info['images'][0] if info.get('images') else None
                            })
        
        return jsonify({
            'status': 'success',
            'data': products
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/save_generated_content', methods=['POST'])
def save_generated_content():
    try:
        data = request.get_json()
        product_id = data["product_id"]
        content_type = data["type"]  # 'image' 或 'video'
        file_url = data["file_url"]
        custom_path = data.get("custom_path", "")
        task_id = data.get("task_id")

        # 验证商品ID格式
        if not product_id.startswith('prod_'):
            return jsonify({'status': 'error', 'error': '无效的商品ID格式'}), 400
        
        # 初始化OSS客户端
        auth = oss2.Auth(OSS_CONFIG['ACCESS_KEY_ID'], OSS_CONFIG['ACCESS_KEY_SECRET'])
        bucket = oss2.Bucket(auth, OSS_CONFIG['ENDPOINT'], OSS_CONFIG['BUCKET_NAME'])
        
        # 生成OSS保存路径
        # 修复：正确处理URL，移除查询参数后再提取扩展名
        from urllib.parse import urlparse
        parsed_url = urlparse(file_url)
        path = parsed_url.path  # 获取路径部分，不含查询参数
        file_ext = path.split('.')[-1].lower() if '.' in path else 'png'  # 默认png格式
        
        # 验证扩展名有效性
        valid_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'mp4', 'avi', 'mov'}
        if file_ext not in valid_exts:
            file_ext = 'png' if content_type == 'image' else 'mp4'  # 使用默认扩展名
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = uuid.uuid4().hex[:6]
        
        # 使用自定义路径或默认路径
        if custom_path:
            save_path = f"{custom_path}gen_{timestamp}_{random_str}.{file_ext}"
            # 确保目录存在
            dir_path = custom_path if custom_path.endswith('/') else f"{custom_path}/"
            if not bucket.object_exists(dir_path):
                bucket.put_object(dir_path, '')
        else:
            if content_type == 'image':
                save_path = f'products/{product_id}/generated_content/images/gen_{timestamp}_{random_str}.{file_ext}'
            else:
                save_path = f'products/{product_id}/generated_content/videos/gen_{timestamp}_{random_str}.{file_ext}'
            # 确保目录存在
            ensure_oss_directories(bucket, product_id)
        
        # 下载文件并上传到OSS
        try:
            print(f"[OSS上传] 开始下载文件: {file_url}")
            response = requests.get(file_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 修复：使用 response.content 而不是 response.raw，更稳定
            file_content = response.content
            print(f"[OSS上传] 文件下载完成，大小: {len(file_content)} bytes")
            
            # 上传到OSS
            result = bucket.put_object(save_path, file_content)
            print(f"[OSS上传] OSS返回状态: {result.status}")
            
            if result.status != 200:
                error_msg = f"OSS上传失败，状态码: {result.status}"
                print(error_msg)
                return jsonify({'status': 'error', 'error': error_msg}), 500
            
            # 返回OSS访问URL
            oss_url = f"https://{OSS_CONFIG['CUSTOM_DOMAIN']}/{save_path}"
            print(f"[OSS上传] 上传成功: {oss_url}")

            if content_type == "video" and task_id:
                db = Task_Db()
                task = db.get_task(task_id)
                if task:
                    merged_result = merge_saved_video_result(
                        task.get("result"), oss_url
                    )
                    task_status = task.get("status") or "completed"
                    db.update_task_status(task_id, task_status, result=merged_result)

            return jsonify(
                {"status": "success", "oss_url": oss_url, "save_path": save_path}
            )

        except requests.exceptions.RequestException as e:
            error_msg = f"下载文件失败: {str(e)}"
            print(error_msg)
            return jsonify({'status': 'error', 'error': error_msg}), 500
            
    except Exception as e:
        error_msg = f"服务器内部错误: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': error_msg}), 500

def ensure_oss_directories(bucket, product_id):
    """确保OSS目录结构存在"""
    required_dirs = [
        f'products/{product_id}/',
        f'products/{product_id}/generated_content/',
        f'products/{product_id}/generated_content/images/',
        f'products/{product_id}/generated_content/videos/'
    ]
    
    for dir_path in required_dirs:
        # OSS通过创建空对象来模拟目录
        if not bucket.object_exists(dir_path):
            bucket.put_object(dir_path, '')

@app.route('/api/oss/categories')
def get_oss_categories():
    """获取所有商品分类"""
    try:
        if not OSS_CONFIG['ACCESS_KEY_ID'] or not OSS_CONFIG['ACCESS_KEY_SECRET']:
            return jsonify({"status": "error", "error": "未配置OSS密钥"}), 500

        local_bucket = _create_oss_bucket()

        prefix = "products/_index/by_category/"
        files = local_bucket.list_objects(prefix=prefix).object_list
        
        # 提取分类名称（去掉.json后缀）
        categories = [
            os.path.splitext(os.path.basename(f.key))[0] 
            for f in files 
            if f.key.endswith('.json')
        ]
        
        return jsonify({
            "status": "success",
            "data": categories
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/oss/products_by_category')
def get_oss_products_by_category():
    """获取指定分类下的所有商品"""
    category = request.args.get('category', '')
    if not category:
        return jsonify({"status": "error", "error": "缺少分类参数"}), 400

    try:
        # 双重解码URL编码
        # local_bucket: 局部作用域的OSS桶对象，用于当前请求的OSS操作
        local_bucket = _create_oss_bucket()
        decoded_category = unquote(unquote(category))
        oss_path = f"products/_index/by_category/{decoded_category}.json"
        
        # 验证文件存在性
        if not local_bucket.object_exists(oss_path):
            return jsonify(
                {
                    "status": "success",
                    "data": [],
                    "message": f"分类'{decoded_category}'暂无商品",
                }
            )

        # 读取OSS文件内容
        obj = local_bucket.get_object(oss_path)
        products = json.loads(obj.read().decode("utf-8"))

        # 验证数据格式
        if not isinstance(products, list):
            raise ValueError("商品数据格式错误，应为数组")

        return jsonify({
            "status": "success",
            "data": products
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "debug": {
                "received_category": category,
                "decoded_category": decoded_category,
                "oss_path": oss_path
            }
        }), 500


def run():
    server = pywsgi.WSGIServer(("0.0.0.0", 5000), app)
    server.serve_forever()


def start():
    MyThread(target=run).start()


if __name__ == '__main__':
    run()








