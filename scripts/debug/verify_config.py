"""
配置验证脚本 - 验证事件驱动架构的配置完整性
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 设置标准输出编码为 UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONFIG_FILE = "opencode.json"

class ConfigValidator:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def log(self, message: str, level: str = "info"):
        if level == "error":
            self.errors.append(message)
        elif level == "warning":
            self.warnings.append(message)
        else:
            self.info.append(message)

    def validate_opencode_json(self) -> bool:
        """验证 opencode.json 配置文件"""
        config_path = self.root_dir / "opencode.json"

        if not config_path.exists():
            self.log(f"❌ opencode.json 不存在", "error")
            return False

        self.log(f"✅ 找到配置文件: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            self.log(f"❌ opencode.json 格式错误: {e}", "error")
            return False

        # 验证 MCP 配置
        if "mcp" not in config:
            self.log("⚠️  缺少 MCP 配置", "warning")
        else:
            mcp = config["mcp"]
            if "web_browser" in mcp:
                self.log("✅ MCP web_browser 已配置")
                if mcp["web_browser"].get("enabled"):
                    self.log("✅ MCP web_browser 已启用")
                else:
                    self.log("⚠️  MCP web_browser 未启用", "warning")

        # 验证 Agent 配置
        if "agent" not in config:
            self.log("❌ 缺少 agent 配置", "error")
            return False

        agents = config["agent"]

        # 检查主 agent
        if "news-collector" not in agents:
            self.log("❌ 缺少主 agent: news-collector", "error")
            return False
        self.log("✅ 主 agent news-collector 已配置")

        # 检查 subagent
        required_subagents = [
            "event-aggregator",
            "validator",
            "timeline-builder",
            "predictor",
            "synthesizer"
        ]

        missing_subagents = []
        for subagent in required_subagents:
            if subagent not in agents:
                missing_subagents.append(subagent)
            else:
                self.log(f"✅ Subagent {subagent} 已配置")

        if missing_subagents:
            self.log(f"❌ 缺少 subagent: {', '.join(missing_subagents)}", "error")
            return False

        # 验证 prompt 文件引用
        self._validate_prompt_files(agents)

        return True

    def _validate_prompt_files(self, agents: Dict) -> None:
        """验证 prompt 文件是否存在"""
        for agent_name, agent_config in agents.items():
            prompt = agent_config.get("prompt", "")
            if prompt.startswith("{file:"):
                file_path = prompt[6:-1]
                full_path = self.root_dir / file_path

                if not full_path.exists():
                    self.log(f"❌ Agent {agent_name} 的 prompt 文件不存在: {file_path}", "error")
                else:
                    self.log(f"✅ Agent {agent_name} 的 prompt 文件存在: {file_path}")

    def validate_subagent_configs(self) -> bool:
        """验证 subagent 配置文件"""
        agents_dir = self.root_dir / ".opencode" / "agents"

        if not agents_dir.exists():
            self.log(f"❌ Subagent 配置目录不存在: {agents_dir}", "error")
            return False

        self.log(f"✅ Subagent 配置目录存在: {agents_dir}")

        required_files = [
            "event-aggregator.md",
            "validator.md",
            "timeline-builder.md",
            "predictor.md",
            "synthesizer.md"
        ]

        missing_files = []
        for file_name in required_files:
            file_path = agents_dir / file_name
            if not file_path.exists():
                missing_files.append(file_name)
            else:
                self.log(f"✅ Subagent 配置文件存在: {file_name}")

        if missing_files:
            self.log(f"❌ 缺少 subagent 配置文件: {', '.join(missing_files)}", "error")
            return False

        return True

    def validate_templates(self) -> bool:
        """验证模板文件"""
        templates_dir = self.root_dir / "templates"

        if not templates_dir.exists():
            self.log(f"⚠️  模板目录不存在: {templates_dir}", "warning")
            return False

        template_file = templates_dir / "report_structure_template.md"
        if template_file.exists():
            self.log(f"✅ 报告结构模板存在: {template_file}")
            return True
        else:
            self.log(f"⚠️  报告结构模板不存在: {template_file}", "warning")
            return False

    def validate_mcp_server(self) -> bool:
        """验证 MCP 服务器配置"""
        mcp_server_file = self.root_dir / "mcp_server" / "web_browser" / "main.py"

        if not mcp_server_file.exists():
            self.log(f"❌ MCP 服务器文件不存在: {mcp_server_file}", "error")
            return False

        self.log(f"✅ MCP 服务器文件存在: {mcp_server_file}")

        # 检查 opencode.json 中的路径配置
        config_path = self.root_dir / "opencode.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        mcp_command = config["mcp"]["web_browser"]["command"]
        if len(mcp_command) > 1:
            mcp_path = mcp_command[1]
            if not (self.root_dir / mcp_path).exists():
                self.log(f"❌ MCP 命令路径不存在: {mcp_path}", "error")
                return False
            self.log(f"✅ MCP 命令路径正确: {mcp_path}")

        return True

    def validate_permissions(self) -> bool:
        """验证权限配置"""
        config_path = self.root_dir / "opencode.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        news_collector = config["agent"]["news-collector"]
        permission = news_collector.get("permission", {})

        # 检查 task 权限
        if "task" not in permission:
            self.log("⚠️  缺少 task 权限配置", "warning")
        elif permission["task"] != {"*": "allow"}:
            self.log("⚠️  task 权限可能不正确，应该是 '*': 'allow'", "warning")
        else:
            self.log("✅ task 权限配置正确")

        # 检查工具权限
        tools = news_collector.get("tools", {})
        required_tools = ["write", "edit", "bash", "read", "grep"]
        for tool in required_tools:
            if tools.get(tool):
                self.log(f"✅ 工具 {tool} 已启用")
            else:
                self.log(f"⚠️  工具 {tool} 未启用", "warning")

        return True

    def run(self) -> Tuple[bool, List[str], List[str], List[str]]:
        """运行所有验证"""
        print("=" * 60)
        print("OpenCode 事件驱动架构 - 配置验证")
        print("=" * 60)
        print()

        results = [
            self.validate_opencode_json(),
            self.validate_subagent_configs(),
            self.validate_templates(),
            self.validate_mcp_server(),
            self.validate_permissions()
        ]

        print()
        print("=" * 60)
        print("验证结果")
        print("=" * 60)
        print()

        # 打印信息
        if self.info:
            for msg in self.info:
                print(msg)
            print()

        # 打印警告
        if self.warnings:
            print("⚠️  警告:")
            for msg in self.warnings:
                print(f"  {msg}")
            print()

        # 打印错误
        if self.errors:
            print("❌ 错误:")
            for msg in self.errors:
                print(f"  {msg}")
            print()

        success = len(self.errors) == 0 and all(results)

        if success:
            print("✅ 所有验证通过！配置正确。")
        else:
            print("❌ 验证失败，请修复上述错误。")

        print()
        print("=" * 60)

        return success, self.info, self.warnings, self.errors


if __name__ == "__main__":
    validator = ConfigValidator()
    success, info, warnings, errors = validator.run()
    exit(0 if success else 1)
