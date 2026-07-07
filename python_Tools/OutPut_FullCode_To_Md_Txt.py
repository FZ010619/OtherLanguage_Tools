"""
================================================================================
脚本名称: AI 友好型全项目代码库导出工具 (GUI版)
适用场景: 
    1. 快速打包整个项目代码，作为 Context（上下文）提供给 LLM（大模型）分析。
    2. 生成项目的目录结构树（Directory Tree），用于技术文档编写。
    3. 备份项目核心代码，过滤掉二进制文件、依赖包和构建产物。
    
核心功能:
    - 智能过滤：自动忽略 .git, node_modules, .venv 等臃肿文件夹及图片、视频等二进制后缀。
    - 文本识别：支持自动检测并导出所有常见的文本/代码文件。
    - 双格式输出：同步生成 .txt（纯文本）和 .md（带 Markdown 代码块格式）两个版本。
    - 目录树生成：自动递归生成漂亮的 ASCII 风格项目目录结构。
    - 现代界面：基于 Tkinter + ttk 提供美化的图形化配置界面，支持多线程导出，不卡顿。

使用说明:
    - 运行脚本，通过 UI 界面设置需要“额外忽略”的文件夹或后缀。
    - 点击“导出”按钮，选择项目根目录，选择保存位置即可。

作者: Fan Zhen
最后修改日期: 2026-04-09
================================================================================
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import threading

# ==================== 配置区 ====================

# 默认忽略的文件夹（导出文件时忽略）
DEFAULT_IGNORE_DIRS = {
    '.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env',
    'dist', 'build', '.idea', '.vscode', 'coverage', 'logs'
}

# 默认忽略的文件后缀
DEFAULT_IGNORE_EXTS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.exe', '.dll', '.so', '.dylib', '.bin',
    '.log', '.tmp', '.cache', '.pyc',
    '.md'
}

# 支持导出的文本/代码文件扩展名
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.sass',
    '.json', '.yaml', '.yml', '.md', '.txt', '.xml', '.sql', '.sh', '.bat',
    '.java', '.cpp', '.c', '.h', '.go', '.rs', '.php', '.rb', '.vue', '.svelte'
}

# 默认输出目录
DEFAULT_OUTPUT_DIR = r"D:\Python_Tools\OutPut_Full_Code"

# 单个文件最大大小（1MB）
MAX_FILE_SIZE = 1 * 1024 * 1024

# ===============================================


def is_text_file(filepath):
    if not os.path.isfile(filepath):
        return False

    ext = os.path.splitext(filepath)[1].lower()
    if ext in TEXT_EXTENSIONS:
        return True

    try:
        with open(filepath, 'r', encoding='utf-8', errors='strict') as f:
            f.read(2048)
        return True
    except:
        return False


def generate_tree(directory, prefix="", is_root=True, tree_ignore_dirs=None):
    if tree_ignore_dirs is None:
        tree_ignore_dirs = set()

    if is_root:
        tree = [os.path.basename(directory) + "/"]
    else:
        tree = []

    try:
        items = sorted([
            item for item in os.listdir(directory)
            if item not in tree_ignore_dirs and not item.startswith('.')
        ])
    except:
        return tree

    for i, item in enumerate(items):
        path = os.path.join(directory, item)
        is_last = i == len(items) - 1
        connector = '└── ' if is_last else '├── '

        if os.path.isdir(path):
            tree.append(f"{prefix}{connector}{item}/")
            new_prefix = prefix + ('    ' if is_last else '│   ')
            tree.extend(generate_tree(path, new_prefix, False, tree_ignore_dirs))
        else:
            tree.append(f"{prefix}{connector}{item}")

    return tree


def export_code(folder_path, output_base_path, extra_ignore_dirs, extra_ignore_exts, tree_ignore_dirs):
    txt_path = output_base_path + ".txt"
    md_path = output_base_path + ".md"
    file_count = 0

    all_ignore_dirs = DEFAULT_IGNORE_DIRS.copy()
    all_ignore_dirs.update(extra_ignore_dirs)

    all_ignore_exts = DEFAULT_IGNORE_EXTS.copy()
    all_ignore_exts.update(extra_ignore_exts)

    try:
        with open(txt_path, 'w', encoding='utf-8') as txt, \
             open(md_path, 'w', encoding='utf-8') as md:

            header = "#" * 80 + "\n"
            header += "# 项目代码库完整导出\n"
            header += f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += f"# 项目路径: {folder_path}\n"
            header += f"# 目录树忽略文件夹: {', '.join(sorted(tree_ignore_dirs))}\n"
            header += f"# 导出忽略文件夹: {', '.join(sorted(all_ignore_dirs))}\n"
            header += f"# 导出忽略后缀: {', '.join(sorted(all_ignore_exts))}\n"
            header += "#" * 80 + "\n\n"

            txt.write(header)
            md.write(f"# 项目代码导出\n\n{header}")

            tree_lines = generate_tree(folder_path, tree_ignore_dirs=tree_ignore_dirs)
            txt.write("## 项目目录结构（已简化）\n\n")
            md.write("## 项目目录结构（已简化）\n\n```\n")
            for line in tree_lines:
                txt.write(line + "\n")
                md.write(line + "\n")
            txt.write("\n" + "=" * 85 + "\n\n")
            md.write("```\n\n---\n\n")

            txt.write("## 文件内容\n\n")
            md.write("## 文件内容\n\n")

            for root_dir, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if d not in all_ignore_dirs and not d.startswith('.')]

                for file in sorted(files):
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in all_ignore_exts or file in all_ignore_dirs:
                        continue

                    file_path = os.path.join(root_dir, file)
                    if os.path.getsize(file_path) > MAX_FILE_SIZE:
                        continue

                    if is_text_file(file_path):
                        rel_path = os.path.relpath(file_path, folder_path)

                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except Exception as e:
                            content = f"[读取失败] {e}\n"

                        title = f"{'='*20} FILE: {rel_path} {'='*20}\n\n"
                        txt.write(title)
                        txt.write(content.rstrip() + "\n")
                        txt.write("\n" + "=" * 60 + "\n\n")

                        md.write(f"### {rel_path}\n\n```text\n")
                        md.write(content.rstrip() + "\n```\n\n")

                        file_count += 1

            txt.write(f"\n# 导出完成！共处理 {file_count} 个文件\n")
            md.write(f"\n---\n\n**导出完成！共处理 {file_count} 个文件**\n")

        return txt_path, md_path, file_count

    except Exception as e:
        raise e


def main():
    root = tk.Tk()
    root.title("代码库导出工具 - 美化版")
    root.geometry("800x900")      # 加大窗口，确保所有内容一屏显示
    root.resizable(True, True)    # 允许用户拖动调整大小
    root.minsize(780, 650)

    # 设置现代主题
    style = ttk.Style()
    style.theme_use('clam')

    # 主容器
    main_frame = ttk.Frame(root, padding=25)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # ==================== 标题 ====================
    title = tk.Label(main_frame, 
                     text="代码库导出工具", 
                     font=("微软雅黑", 22, "bold"), 
                     fg="#2c3e50")
    title.pack(pady=(0, 20))

    subtitle = tk.Label(main_frame, 
                        text="将整个项目快速打包成 TXT + MD 文件，适合喂给 AI 大模型",
                        font=("微软雅黑", 10), 
                        fg="#7f8c8d")
    subtitle.pack(pady=(0, 25))

    # ==================== 默认配置区 ====================
    default_frame = ttk.LabelFrame(main_frame, text=" 默认忽略配置（固定生效）", padding=15)
    default_frame.pack(fill="x", pady=8)

    # 忽略文件夹
    ttk.Label(default_frame, text="忽略的文件夹：", font=("微软雅黑", 10, "bold")).grid(row=0, column=0, sticky="w", pady=4)
    ttk.Label(default_frame, text=", ".join(sorted(DEFAULT_IGNORE_DIRS)), 
              foreground="#2980b9", wraplength=680).grid(row=0, column=1, sticky="w", pady=4, padx=10)

    # 忽略后缀
    ttk.Label(default_frame, text="忽略的文件后缀：", font=("微软雅黑", 10, "bold")).grid(row=1, column=0, sticky="w", pady=4)
    ttk.Label(default_frame, text=", ".join(sorted(DEFAULT_IGNORE_EXTS)), 
              foreground="#2980b9", wraplength=680).grid(row=1, column=1, sticky="w", pady=4, padx=10)

    # ==================== 目录树忽略区 ====================
    tree_frame = ttk.LabelFrame(main_frame, text=" 目录树显示优化（推荐填写，让目录结构更清晰）", padding=15)
    tree_frame.pack(fill="x", pady=10)

    ttk.Label(tree_frame, text="生成目录树时忽略的文件夹（用英文逗号分隔）：", 
              font=("微软雅黑", 10, "bold")).pack(anchor="w")

    tree_ignore_entry = ttk.Entry(tree_frame, font=("微软雅黑", 11), width=90)
    tree_ignore_entry.pack(fill="x", pady=8, ipady=6)
    tree_ignore_entry.insert(0, ".venv,venv,node_modules,.git,__pycache__,dist,build")

    ttk.Label(tree_frame, text="提示：这些文件夹不会显示在目录树中，但文件内容仍可正常导出", 
              foreground="#7f8c8d", font=("微软雅黑", 9)).pack(anchor="w")

    # ==================== 本次额外忽略区 ====================
    extra_frame = ttk.LabelFrame(main_frame, text=" 本次导出额外忽略设置（仅本次有效）", padding=15)
    extra_frame.pack(fill="x", pady=10)

    # 额外忽略文件夹
    ttk.Label(extra_frame, text="额外忽略的文件夹：", font=("微软雅黑", 10, "bold")).pack(anchor="w")
    extra_dirs_entry = ttk.Entry(extra_frame, font=("微软雅黑", 11), width=90)
    extra_dirs_entry.pack(fill="x", pady=8, ipady=6)
    extra_dirs_entry.insert(0, "backup,old_version,test_data")

    # 额外忽略后缀
    ttk.Label(extra_frame, text="额外忽略的文件后缀（带点，用逗号分隔）：", font=("微软雅黑", 10, "bold")).pack(anchor="w", pady=(12,4))
    extra_exts_entry = ttk.Entry(extra_frame, font=("微软雅黑", 11), width=90)
    extra_exts_entry.pack(fill="x", pady=8, ipady=6)
    extra_exts_entry.insert(0, ".log,.tmp,.png,.pdf")

    # ==================== 导出按钮 ====================
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=30)

    export_button = ttk.Button(
        button_frame,
        text="选择项目文件夹并开始导出",
        style="Accent.TButton",
        command=lambda: threading.Thread(target=start_export, daemon=True).start()
    )
    export_button.pack(ipadx=40, ipady=14)

    # 底部说明
    footer = tk.Label(main_frame, 
                      text="导出后将同时生成 .txt 和 .md 两个文件 • 额外设置仅本次生效",
                      font=("微软雅黑", 9), 
                      fg="#95a5a6")
    footer.pack(pady=10)

    # ==================== 执行导出函数 ====================
    def start_export():
        folder_path = filedialog.askdirectory(title="选择要导出的项目文件夹")
        if not folder_path:
            return

        tree_ignore_input = tree_ignore_entry.get().strip()
        tree_ignore_dirs = {i.strip() for i in tree_ignore_input.split(",") if i.strip()}

        extra_dirs_input = extra_dirs_entry.get().strip()
        extra_ignore_dirs = {i.strip() for i in extra_dirs_input.split(",") if i.strip()}

        extra_exts_input = extra_exts_entry.get().strip()
        extra_ignore_exts = {i.strip().lower() for i in extra_exts_input.split(",") if i.strip()}

        default_name = f"{os.path.basename(folder_path)}_full_codebase"

        output_path = filedialog.asksaveasfilename(
            title="保存导出文件",
            initialdir=DEFAULT_OUTPUT_DIR,
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )

        if not output_path:
            return

        output_base = os.path.splitext(output_path)[0]

        try:
            txt_path, md_path, count = export_code(
                folder_path, output_base, extra_ignore_dirs, extra_ignore_exts, tree_ignore_dirs
            )

            messagebox.showinfo(
                "导出成功",
                f"✅ 导出完成！\n\n"
                f"共处理 {count} 个文件\n\n"
                f"TXT 文件：\n{txt_path}\n\n"
                f"MD 文件：\n{md_path}"
            )
        except Exception as e:
            messagebox.showerror("导出失败", f"发生错误：\n{str(e)}")

    root.mainloop()


if __name__ == "__main__":
    main()