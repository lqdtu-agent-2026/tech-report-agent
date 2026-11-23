import os
import json
import glob
import yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Khởi tạo client kết nối tới OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://github.com/your-username/my-openrouter-agent",
        "X-Title": "My OpenRouter Skill Agent",
    }
)

MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-4-neon")


def discover_skills(skills_dir="skills"):
    """Quét tất cả file SKILL.md và trích xuất phần YAML frontmatter."""
    skills = {}
    for filepath in glob.glob(os.path.join(skills_dir, "**", "*.md"), recursive=True):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                meta = yaml.safe_load(parts[1]) or {}
                skill_name = meta.get("name", os.path.basename(os.path.dirname(filepath)))
                skills[skill_name] = {
                    "name": skill_name,
                    "description": meta.get("description", "Không có mô tả."),
                    "instructions": parts[2].strip(),
                    "path": filepath
                }
    return skills


def build_system_prompt(skills):
    """Tạo system prompt liệt kê danh sách skill hiện có (chỉ nạp tên & mô tả)."""
    skill_list = "\n".join(
        [f"- **{s['name']}**: {s['description']}" for s in skills.values()]
    )
    return f"""Bạn là một AI Agent thông minh có khả năng sử dụng các kỹ năng (Skills) chuyên biệt.

Danh sách các Skills hiện có:
{skill_list if skill_list else "Chưa có skill nào."}

QUY TẮC:
1. Khi yêu cầu của người dùng khớp với mô tả của một Skill ở trên, hãy gọi công cụ `load_skill` với `skill_name` tương ứng ĐỂ ĐỌC HƯỚNG DẪN CHI TIẾT trước khi trả lời.
2. Sau khi nhận được nội dung hướng dẫn từ `load_skill`, hãy tuân thủ nghiêm ngặt từng bước trong tài liệu đó."""


def run_agent(user_prompt):
    skills = discover_skills()
    system_prompt = build_system_prompt(skills)

    # Định nghĩa tool để Agent tự động nạp file .md khi cần
    tools = [
        {
            "type": "function",
            "function": {
                "name": "load_skill",
                "description": "Nạp nội dung hướng dẫn chi tiết của một skill từ file Markdown.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "Tên chính xác của skill cần nạp",
                            "enum": list(skills.keys()) if skills else ["none"]
                        }
                    },
                    "required": ["skill_name"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Bước 1: Gửi request đầu tiên để Agent quyết định có cần dùng skill không
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools if skills else None,
        tool_choice="auto" if skills else None
    )

    msg = response.choices[0].message

    # Bước 2: Nếu Agent yêu cầu gọi tool `load_skill`
    if msg.tool_calls:
        messages.append(msg)
        for tool_call in msg.tool_calls:
            if tool_call.function.name == "load_skill":
                args = json.loads(tool_call.function.arguments)
                skill_name = args.get("skill_name")
                print(f"[Agent] Đang kích hoạt skill: {skill_name}...")

                skill_data = skills.get(skill_name)
                tool_result = (
                    skill_data["instructions"]
                    if skill_data
                    else f"Không tìm thấy skill '{skill_name}'."
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

        # Bước 3: Gửi lại nội dung file .md cho OpenRouter để sinh câu trả lời cuối cùng
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        return final_response.choices[0].message.content

    return msg.content


if __name__ == "__main__":
    print("=== OpenRouter Skill Agent (Gõ 'exit' để thoát) ===")
    while True:
        user_input = input("\nBạn: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            break
        reply = run_agent(user_input)
        print(f"\nAgent:\n{reply}")