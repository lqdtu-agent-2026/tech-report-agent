import os
import json
import glob
import yaml
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://github.com/lqdtu-agent-2026/tech-report-agent",
        "X-Title": "Tech Report Skill Agent",
    }
)

MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")


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


def read_pdf_file(file_path, max_pages=30):
    """Trích xuất văn bản từ file PDF trên máy."""
    # Xử lý trường hợp user kéo thả file vào terminal bị dính dấu nháy đơn/kép
    clean_path = file_path.strip().strip("'\"")

    if not os.path.exists(clean_path):
        return f"Lỗi: Không tìm thấy file tại đường dẫn '{clean_path}'. Hãy kiểm tra lại đường dẫn."

    if not clean_path.lower().endswith(".pdf"):
        return f"Lỗi: File '{clean_path}' không phải là định dạng .pdf."

    try:
        reader = PdfReader(clean_path)
        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)

        extracted_text = [f"Thông tin file: {os.path.basename(clean_path)} (Tổng số trang: {total_pages})\n"]
        for i in range(pages_to_read):
            page_text = reader.pages[i].extract_text() or "[Trang này không có văn bản hoặc là ảnh scan]"
            extracted_text.append(f"--- TRANG {i + 1} ---\n{page_text}")

        if total_pages > max_pages:
            extracted_text.append(f"\n[Lưu ý: Đã giới hạn đọc {max_pages}/{total_pages} trang đầu để tiết kiệm token.]")

        return "\n".join(extracted_text)
    except Exception as e:
        return f"Lỗi hệ thống khi đọc file PDF: {str(e)}"


def build_system_prompt(skills):
    """Tạo system prompt hướng dẫn Agent cách phối hợp cả 2 tool."""
    skill_list = "\n".join(
        [f"- **{s['name']}**: {s['description']}" for s in skills.values()]
    )
    return f"""Bạn là một AI Agent chuyên phân tích báo cáo kỹ thuật (Tech Report Agent) và xử lý tài liệu.

Danh sách các Skills hiện có:
{skill_list if skill_list else "Chưa có skill nào."}

QUY TẮC HOẠT ĐỘNG:
1. **Đọc tài liệu PDF**: Khi người dùng cung cấp đường dẫn file `.pdf` (ví dụ: `report.pdf` hoặc `/home/.../file.pdf`), hãy gọi công cụ `read_pdf` để lấy nội dung tài liệu trước.
2. **Sử dụng Skill**: Khi yêu cầu của người dùng khớp với mô tả của một Skill ở trên, hãy gọi công cụ `load_skill` với `skill_name` tương ứng để đọc quy trình hướng dẫn chi tiết.
3. Bạn có thể gọi cả `read_pdf` và `load_skill` cùng lúc hoặc lần lượt trước khi tổng hợp câu trả lời cuối cùng.
4. Luôn bám sát nội dung thực tế trích xuất từ PDF, không tự bịa thêm số liệu không có trong tài liệu."""


def run_agent(user_prompt):
    skills = discover_skills()
    system_prompt = build_system_prompt(skills)

    # Khai báo danh sách tools (luôn có read_pdf, và có load_skill nếu thư mục skills có file)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_pdf",
                "description": "Đọc và trích xuất nội dung văn bản từ một file PDF cục bộ trên máy tính.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Đường dẫn tương đối hoặc tuyệt đối tới file PDF (ví dụ: 'docs/report.pdf')"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
    ]

    if skills:
        tools.append({
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
                            "enum": list(skills.keys())
                        }
                    },
                    "required": ["skill_name"]
                }
            }
        })

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Vòng lặp tối đa 5 bước suy luận/gọi tool để tránh lặp vô hạn
    for _ in range(5):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message

        # Nếu Agent không gọi thêm tool nào nữa -> Trả kết quả cuối cùng
        if not msg.tool_calls:
            return msg.content

        # Lưu yêu cầu gọi tool của Agent vào lịch sử hội thoại
        messages.append(msg)

        # Thực thi từng tool mà Agent yêu cầu
        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if func_name == "read_pdf":
                file_path = args.get("file_path", "")
                print(f"[Agent] Đang đọc file PDF: {file_path}...")
                tool_result = read_pdf_file(file_path)

            elif func_name == "load_skill":
                skill_name = args.get("skill_name", "")
                print(f"[Agent] Đang kích hoạt skill: {skill_name}...")
                skill_data = skills.get(skill_name)
                tool_result = (
                    skill_data["instructions"]
                    if skill_data
                    else f"Không tìm thấy skill '{skill_name}'."
                )
            else:
                tool_result = f"Tool '{func_name}' không được hỗ trợ."

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

    return "Agent đã đạt giới hạn số bước xử lý tối đa cho một lượt hỏi."


if __name__ == "__main__":
    print("=== Tech Report Skill Agent (Gõ 'exit' để thoát) ===")
    print("Mẹo: Bạn có thể kéo thả trực tiếp file PDF vào cửa sổ Terminal này!\n")
    while True:
        user_input = input("Bạn: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            break
        if not user_input.strip():
            continue

        try:
            reply = run_agent(user_input)
            print(f"\nAgent:\n{reply}\n")
        except Exception as e:
            print(f"\n[Lỗi]: {e}\n")