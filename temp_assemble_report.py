#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys


def assemble_report():
    parts_dir = (
        "./output/report_20260131_004345/国际金融新闻/2026-01-31/资讯汇总与摘要/.parts"
    )
    output_file = "./output/report_20260131_004345/国际金融新闻/2026-01-31/资讯汇总与摘要/国际金价突破5200美元.md"

    # 定义各部分文件的顺序
    section_files = [
        ("01-summary.md", "事件摘要"),
        ("02-news.md", "新闻来源"),
        ("03-validation.md", "真实性验证"),
        ("04-timeline.md", "事件时间轴"),
        ("05-prediction.md", "趋势预测"),
        ("06-images.md", "相关图片"),
    ]

    try:
        # 创建输出文件并写入标题
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write("# 国际金价突破5200美元\n\n")
            out_f.write(f"生成时间: 2026-01-31\n")
            out_f.write(f"事件类别: 国际金融\n")
            out_f.write(f"数据来源: 新闻数据分析系统\n\n")
            out_f.write("---\n\n")

            # 依次写入各部分内容
            for filename, title in section_files:
                filepath = os.path.join(parts_dir, filename)

                if os.path.exists(filepath):
                    out_f.write(f"## {title}\n\n")

                    # 读取并写入部分内容
                    with open(filepath, "r", encoding="utf-8") as part_f:
                        content = part_f.read()
                        out_f.write(content)

                    out_f.write("\n\n---\n\n")
                    print(f"已添加部分: {title}")
                else:
                    print(f"警告: 文件不存在 {filepath}")

        print(f"报告已成功组装: {output_file}")

        # 计算总字数（简单统计）
        total_words = 0
        with open(output_file, "r", encoding="utf-8") as f:
            text = f.read()
            # 简单统计中文字符和英文单词
            chinese_chars = len([c for c in text if "\u4e00" <= c <= "\u9fff"])
            english_words = len([w for w in text.split() if w])
            total_words = chinese_chars + english_words

        print(f"报告总字数: 约 {total_words} 字")

        return {"success": True, "output_file": output_file, "total_words": total_words}

    except Exception as e:
        print(f"组装报告时出错: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    result = assemble_report()
    sys.exit(0 if result["success"] else 1)
