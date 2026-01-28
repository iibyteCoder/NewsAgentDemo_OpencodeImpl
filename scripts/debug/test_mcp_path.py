"""测试 MCP 服务器路径"""
import os
import sys
import subprocess


# 检查 Python 解释器路径
python_exe = ".venv/Scripts/python.exe"
if os.path.exists(python_exe):
    print(f"[OK] Python path exists: {python_exe}")
    print(f"   Absolute path: {os.path.abspath(python_exe)}")
else:
    print(f"[FAIL] Python path NOT found: {python_exe}")
    # 尝试其他路径
    alt_paths = [
        ".venv/bin/python.exe",
        "venv/Scripts/python.exe",
        "venv/bin/python.exe",
        ".venv\\Scripts\\python.exe",
    ]
    for alt in alt_paths:
        if os.path.exists(alt):
            print(f"[OK] Alternative found: {alt}")
            python_exe = alt
            break

print(f"\nUsing Python: {python_exe}")

# 检查 main.py 路径
main_py = "mcp_server/web_browser/main.py"
if os.path.exists(main_py):
    print(f"[OK] Main.py exists: {main_py}")
else:
    # 尝试反斜杠
    main_py_alt = "mcp_server\\web_browser\\main.py"
    if os.path.exists(main_py_alt):
        print(f"[OK] Main.py exists (with backslash): {main_py_alt}")
        main_py = main_py_alt
    else:
        print(f"[FAIL] Main.py NOT found: {main_py}")

# 测试命令能否启动
print("\n" + "=" * 60)
print("Testing MCP server startup...")
print("=" * 60)

cmd = [python_exe, main_py]
print(f"Command: {' '.join(cmd)}")

try:
    # 使用短超时来测试服务器能否启动
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=2,
        cwd=os.getcwd()
    )
    print(f"\nReturn code: {result.returncode}")
    if result.stdout:
        print(f"Stdout: {result.stdout[:200]}")
    if result.stderr:
        print(f"Stderr: {result.stderr[:200]}")
except subprocess.TimeoutExpired:
    print("\n[OK] Server started successfully (timed out as expected)")
    print("   (MCP servers run indefinitely waiting for stdin)")
except Exception as e:
    print(f"\n[ERROR] {e}")

print("\n" + "=" * 60)
print("Recommended opencode.json command:")
print("=" * 60)

# 推荐配置
if os.name == 'nt':  # Windows
    recommended_python = ".venv\\Scripts\\python.exe"
    recommended_main = "mcp_server\\web_browser\\main.py"
else:
    recommended_python = ".venv/bin/python"
    recommended_main = "mcp_server/web_browser/main.py"

print(f'["{recommended_python}", "{recommended_main}"]')
