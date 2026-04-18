import sys
sys.path.append('/Users/xumingyu/aigc')
from llm import nlp_langchain
try:
    print("Testing question...")
    ans = nlp_langchain.question("你好", uid="user_1")
    print(f"ANSWER: {ans}")
except Exception as e:
    import traceback
    traceback.print_exc()
