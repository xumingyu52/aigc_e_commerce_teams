import os
import re
from funasr import AutoModel

def post_process(text):

    if not text:
        return ""
    
    #修复“数字 + 斤，装”的问题：把“4斤，装”变成“4斤装”
    text = re.sub(r'(\d+斤)，装', r'\1斤装', text)
    
    #修复“不1样”这种生硬的转换（如有需要可添加更多）
    text = text.replace("不1样", "不一样")
    text = text.replace("1号链接", "一号链接")
    
    #常见的单位连滞修复（例如：5，瓶 -> 5瓶）
    text = re.sub(r'(\d+)，(瓶|袋|听|件|个)', r'\1\2', text)
    
    return text

# 1. 加载模型
print("正在加载模型...")
model = AutoModel(model="paraformer-zh", model_revision="v2.0.4",
                  vad_model="fsmn-vad", vad_model_revision="v2.0.4",
                  punc_model="ct-punc-c", punc_model_revision="v2.0.4")

# 2. 读取热词
hotword_file = "asr/funasr/data/hotword.txt"
hotwords = ""
if os.path.exists(hotword_file):
    with open(hotword_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        hotwords = " ".join(lines)
    print(f"已加载热词库（共 {len(lines)} 个词）")

# 尝试开启内置 ITN 功能
param_dict = {
    "sentence_timestamp": False, 
    "hotword": hotwords,
    "itn": True  # 开启反向文本标准化
}

# 3. 指定音频并识别
wav_path = "asr/funasr/test.wav"

if os.path.exists(wav_path):
    print(f"正在识别文件: {wav_path}")
    res = model.generate(input=wav_path, is_final=True, **param_dict)
    
    raw_text = res[0]['text']
    # 执行后处理
    final_text = post_process(raw_text)
    
    print("\n" + "="*40)
    print("识别内容:", final_text)
    print("="*40 + "\n")
else:
    print(f"找不到音频文件: {wav_path}")