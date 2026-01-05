import os
import base64
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent 
from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

# --- LOGGER TÍNH TIỀN (Giữ nguyên để kiểm soát phí) ---
PRICING = {"input": 0.05 / 1_000_000, "output": 0.40 / 1_000_000}

class CostLogger(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            p_tokens = usage.get("prompt_tokens", 0)
            c_tokens = usage.get("completion_tokens", 0)
            cost = (p_tokens * PRICING["input"]) + (c_tokens * PRICING["output"])
            print(f"\n[CHI PHÍ]: ${cost:.6f} (~{cost * 25000:.2f} VNĐ)")

# --- TOOL GITHUB TÙY CHỈNH ---
@tool
def upload_to_github(file_content: str, file_name: str) -> str:
    """
    Tự động upload nội dung văn bản lên repo CHANVO04/AI-Agent.
    - file_content: Nội dung bên trong file.
    - file_name: Tên file (ví dụ: 'test_agent.txt').
    """
    token = os.getenv("GITHUB_TOKEN")
    repo = "CHANVO04/AI-Agent"
    url = f"https://api.github.com/repos/{repo}/contents/{file_name}"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # GitHub API yêu cầu nội dung phải là Base64
    content_encoded = base64.b64encode(file_content.encode()).decode()
    
    data = {
        "message": "AI Agent automated upload",
        "content": content_encoded,
        "branch": "main" 
    }
    
    res = requests.put(url, headers=headers, json=data)
    if res.status_code in [200, 201]:
        return f"Thành công! File {file_name} đã có trên GitHub."
    return f"Lỗi: {res.json().get('message')}"

def run_github_agent():
    # Sử dụng GPT-5-nano để tiết kiệm tiền
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0, callbacks=[CostLogger()])
    
    tools = [upload_to_github]
    
    # Cấu trúc create_agent bạn đang dùng ổn định nhất
    agent_graph = create_agent(llm, tools)
    
    # Chỉ dẫn hệ thống để Agent không làm sai
    system_msg = SystemMessage(content="You are a GitHub Agent. Use 'upload_to_github' for all upload requests.")
    user_msg = HumanMessage(content="Hãy truy cập repo https://github.com/CHANVO04/AI-Agent.git và upload 1 file txt tên là 'hello_ai.txt' với nội dung 'Xin chao tu AI Agent'.")
    
    print("--- ĐANG THỰC THI ---")
    stream = agent_graph.stream({"messages": [system_msg, user_msg]}, stream_mode="values")
    
    for step in stream:
        step["messages"][-1].pretty_print()

if __name__ == "__main__":
    run_github_agent()