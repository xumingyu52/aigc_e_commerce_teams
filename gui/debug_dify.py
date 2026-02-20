import requests
import json

url = 'https://api.dify.ai/v1/workflows/run'
headers = {'Authorization': 'Bearer app-LLqziYb1p0ySdDXKTrOa0RQt'}
data = {
    'inputs': {'basic_instruction': '测试薯片文案'},
    'response_mode': 'blocking',
    'user': 'abc-123'
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    try:
        json_data = response.json()
        print("Response JSON:")
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
        
        outputs = json_data.get('data', {}).get('outputs', {})
        print("\nOutputs keys:", list(outputs.keys()))
        
        content = ''
        for k in ['red_content', 'content', 'text', 'output', 'result', 'reply']:
            if k in outputs:
                content = outputs[k]
                print(f"Found content in key '{k}': {content[:50]}...")
                break
        
        if not content:
            print("WARNING: No content found in known keys!")
            
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print("Raw text:", response.text)

except Exception as e:
    print(f"Request failed: {e}")
