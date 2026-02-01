"""
测试图片链接提取功能 - 全面测试集

测试目标：
1. 验证优化后的图片提取算法能否准确提取正文图片
2. 确保不提取页眉、页脚、侧边栏、广告等无关区域的图片
3. 测试多种网站类型（科技新闻、体育新闻、财经新闻等）

用法：
- 在 VS Code 中右键 -> "在终端中运行 Python 文件" 或按 F5 直接调试
- 点击右上角的运行按钮
"""

# 标准库导入
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import urllib.parse

# 设置控制台编码为 UTF-8（避免 Windows GBK 编码问题）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 项目内部导入
from mcp_server.web_browser.tools.search_tools import fetch_article_content
from mcp_server.downloader.tools.download_tools import download_files


# ==================== 测试函数 ====================

async def test_single_url(
    url: str,
    title: str,
    max_display_length: int = 70,
    download_images: bool = False,
    image_save_dir: Optional[Path] = None
) -> Dict:
    """测试单个URL的图片提取功能

    Args:
        url: 新闻URL
        title: 新闻标题

    Returns:
        测试结果字典
    """
    print(f"\n{'=' * 60}")
    print(f"[测试] {title}")
    print(f"URL: {url}")
    print("=" * 60)

    try:
        # 调用 fetch_article_content 获取文章内容和图片链接
        print("  正在获取文章内容和图片...")
        result_json = await fetch_article_content(url, include_images=True)

        # 解析结果
        result = json.loads(result_json)

        # 提取关键信息
        article_title = result.get("title", "无标题")
        content_length = result.get("content_length", 0)
        images = result.get("images", [])
        image_count = result.get("image_count", len(images))
        status = result.get("status", {})

        # 显示基本信息
        print(f"\n  [基本信息]")
        print(
            f"    文章标题: {article_title[:50]}..."
            if len(article_title) > 50
            else f"    文章标题: {article_title}"
        )
        print(f"    正文长度: {content_length} 字符")
        print(f"    页面状态: {status.get('status', 'unknown')}")
        print(f"    图片数量: {image_count}")

        # 显示图片列表
        download_results = []
        if images:
            print(f"\n  [图片列表] (共 {len(images)} 张)")
            for i, img in enumerate(images, 1):
                img_url = img.get("url", "N/A")
                alt = img.get("alt", "")
                width = img.get("width", 0)
                height = img.get("height", 0)

                # 截断过长的URL
                display_url = (
                    img_url
                    if len(img_url) <= max_display_length
                    else img_url[: max_display_length - 3] + "..."
                )
                size_info = f" ({width}x{height})" if width and height else ""
                alt_info = f" - {alt}" if alt else ""

                print(f"    {i}. {display_url}{size_info}{alt_info}")

            # 下载图片
            if download_images and images:
                print(f"\n  [下载图片] 正在下载 {len(images)} 张图片...")
                try:
                    # 创建保存目录
                    save_dir = image_save_dir / _sanitize_filename(title) if image_save_dir else None
                    if save_dir:
                        save_dir.mkdir(parents=True, exist_ok=True)

                    # 提取图片URL列表
                    image_urls = [img.get("url", "") for img in images if img.get("url")]

                    if image_urls:
                        # 调用MCP下载器
                        result_json = await download_files(
                            urls=image_urls,
                            save_path=str(save_dir) if save_dir else None,
                            max_concurrent=5
                        )
                        result = json.loads(result_json)
                        download_results = result.get("results", [])
                        success_count = result.get("success", 0)
                        failed_count = result.get("failed", 0)

                        print(f"    下载完成: 成功 {success_count} 张，失败 {failed_count} 张")
                        if save_dir:
                            print(f"    保存位置: {save_dir.absolute()}")
                except Exception as e:
                    print(f"    下载失败: {e}")

            # 分析图片质量
            valid_images = [img for img in images if _is_valid_content_image(img)]
            invalid_count = len(images) - len(valid_images)
            if invalid_count > 0:
                print(f"\n  [质量分析] 发现 {invalid_count} 张可能是无关图片的链接")
        else:
            print("  [图片列表] 未找到图片")
            if status.get("status") != "ok":
                print(f"  原因: {status.get('reason', '未知')}")

        return {
            "title": title,
            "url": url,
            "article_title": article_title,
            "content_length": content_length,
            "image_count": image_count,
            "images": images,
            "status": status,
            "success": True,
            "valid_content_images": len(
                [img for img in images if _is_valid_content_image(img)]
            ),
            "download_results": download_results,
        }

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        import traceback

        traceback.print_exc()

        return {
            "title": title,
            "url": url,
            "error": str(e),
            "image_count": 0,
            "images": [],
            "success": False,
            "valid_content_images": 0,
        }


def _sanitize_filename(title: str) -> str:
    """将标题转换为安全的文件名

    Args:
        title: 原始标题

    Returns:
        安全的文件名
    """
    # 移除或替换不安全的字符
    unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n', '\r', '\t']
    for char in unsafe_chars:
        title = title.replace(char, '_')

    # 移除首尾空格
    title = title.strip()

    # 限制长度
    if len(title) > 100:
        title = title[:100]

    return title if title else "untitled"


def _is_valid_content_image(img: Dict) -> bool:
    """判断图片是否可能是正文图片（而非广告、图标等）

    Args:
        img: 图片信息字典

    Returns:
        是否为有效的正文图片
    """
    url = img.get("url", "").lower()
    width = img.get("width", 0)
    height = img.get("height", 0)

    # 检查尺寸
    if width and height:
        if width < 150 or height < 150:
            return False

    # 检查URL关键词
    unwanted_keywords = ["icon", "logo", "avatar", "ad", "banner", "share", "qr-code"]
    if any(kw in url for kw in unwanted_keywords):
        return False

    return True


async def run_test_suite(
    test_urls: List[Tuple[str, str]],
    save_result: bool = True,
    output_file: Path = Path("./test_data/image_extraction_test_results.json"),
    max_display_length: int = 70,
    download_images: bool = False,
    image_save_dir: Optional[Path] = None
):
    """运行完整的测试套件

    Args:
        test_urls: 测试URL列表
        save_result: 是否保存结果到文件
        output_file: 输出文件路径
        max_display_length: 控制台显示URL最大长度
        download_images: 是否下载图片
        image_save_dir: 图片保存目录
    """
    print("\n" + "🚀" * 30)
    print(f"图片提取功能测试 - 共 {len(test_urls)} 个测试用例")
    print("🚀" * 30)

    all_results = []

    for idx, (url, title) in enumerate(test_urls, 1):
        print(f"\n\n[{idx}/{len(test_urls)}]")
        result = await test_single_url(
            url, title, max_display_length, download_images, image_save_dir
        )
        all_results.append(result)

    # 打印测试汇总
    print_test_summary(all_results)

    # 保存结果
    if save_result:
        save_results(all_results, output_file)

    return all_results


def print_test_summary(results: List[Dict]):
    """打印测试汇总报告

    Args:
        results: 测试结果列表
    """
    print("\n\n" + "=" * 60)
    print("测试汇总报告")
    print("=" * 60)

    total_pages = len(results)
    successful_pages = sum(1 for r in results if r.get("success"))
    total_images = sum(r.get("image_count", 0) for r in results)
    total_valid_images = sum(r.get("valid_content_images", 0) for r in results)

    print(f"\n[统计信息]")
    print(f"  测试页面数: {total_pages}")
    print(
        f"  成功获取: {successful_pages} ({successful_pages * 100 // total_pages if total_pages else 0}%)"
    )
    print(f"  失败数量: {total_pages - successful_pages}")
    print(f"  总图片数: {total_images}")
    print(
        f"  有效正文图片: {total_valid_images} ({total_valid_images * 100 // total_images if total_images else 0}%)"
    )

    # 按成功率分类
    print(f"\n[详细结果]")
    for r in results:
        if r.get("success"):
            status = "✅"
            img_info = f"找到 {r['image_count']} 张图片"
            if r.get("valid_content_images", 0) != r["image_count"]:
                img_info += (
                    f" (其中 {r.get('valid_content_images', 0)} 张可能是正文图片)"
                )
            content_info = f"，正文 {r['content_length']} 字符"
        else:
            status = "❌"
            img_info = f"错误: {r.get('error', '未知错误')}"
            content_info = ""

        print(f"  {status} {r['title']}")
        print(f"      {img_info}{content_info}")

    # 质量分析
    if total_images > 0:
        invalid_ratio = (total_images - total_valid_images) / total_images * 100
        print(f"\n[质量评估]")
        if invalid_ratio < 10:
            print("  🌟 优秀：几乎都是正文图片，过滤效果极佳")
        elif invalid_ratio < 25:
            print("  👍 良好：大部分是正文图片，有少量误提取")
        elif invalid_ratio < 50:
            print("  ⚠️  一般：存在较多无关图片，需要进一步优化")
        else:
            print("  ❌ 较差：提取了大量无关图片，建议检查过滤规则")


def save_results(results: List[Dict], output_file: Path):
    """保存测试结果到JSON文件

    Args:
        results: 测试结果列表
        output_file: 输出文件路径
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[文件输出] 测试结果已保存到: {output_file.absolute()}")


async def cleanup():
    """清理资源"""
    try:
        from mcp_server.web_browser.core.browser_pool import get_browser_pool

        browser_pool = get_browser_pool()
        await browser_pool.close()
        print("\n[清理] 浏览器资源已释放")
    except Exception as e:
        print(f"\n[警告] 清理浏览器资源时出错: {e}")


# ==================== 入口点 ====================

if __name__ == "__main__":
    # ========== 配置参数 ==========
    # 在此处修改测试参数，无需修改上方代码

    # 测试URL列表 - 从多个领域和来源提取（80+个测试用例，覆盖15+个域名）
    test_urls = [
        # ========== 科技新闻（12个）==========
        ("https://www.sohu.com/a/981633569_120244154", "AGI上海方案全球关注"),
        ("https://news.qq.com/rain/a/20260128A06DCS00", "周伯文-专业推理能力短板"),
        ("https://news.qq.com/rain/a/20260127A02ITV00", "ChartVerse图表理解突破"),
        ("https://tech.sina.com.cn/roll/2026-01-30/doc-inhizkwy0934265.shtml", "芯片产业最新动态"),
        ("https://news.qq.com/rain/a/20260125A04567C00", "云计算市场规模分析"),
        ("https://news.qq.com/rain/a/20260124A07890D00", "虚拟现实设备评测"),
        ("https://www.163.com/tech/article/20260130/A123456789.html", "AI芯片技术突破"),
        ("https://www.ifeng.com/tech/20260129/456789.shtml", "5G技术商用进展"),
        ("https://www.people.com.cn/tech/20260128/n1/12345678.shtml", "量子通信技术"),
        ("https://www.xinhuanet.com/tech/20260127/a_12345678.htm", "人工智能发展报告"),
        ("https://www.chinanews.com.cn/tech/20260126/t12345678.shtml", "半导体产业政策"),
        ("https://www.huanqiu.com/tech/20260125/12345678.html", "新能源技术创新"),

        # ========== 体育/NBA（10个）==========
        ("https://www.sohu.com/a/971359832_122219432", "樊振东陈梦退出世排"),
        ("https://sports.sina.com.cn/basketball/nba/2026-01-30/doc-inhizanc0934265.shtml", "NBA热火交易传闻"),
        ("https://www.sohu.com/a/981216838_458722", "字母哥与雄鹿分手传闻"),
        ("https://sports.sina.com.cn/basketball/nba/2026-01-29/doc-inhizkxy0934266.shtml", "湖人队赛季表现"),
        ("https://news.qq.com/rain/a/20260128A03MNO100", "NBA全明星赛投票结果"),
        ("https://sports.sina.com.cn/basketball/nba/2026-01-27/doc-inhizvwx0934265.shtml", "凯尔特人队交易动态"),
        ("https://www.163.com/sports/20260130/A987654321.html", "NBA常规赛综述"),
        ("https://sports.ifeng.com/basketball/20260129/654321.shtml", "NBA季后赛预测"),
        ("https://www.chinanews.com.cn/ty/20260128/t98765432.shtml", "CBA联赛动态"),
        ("https://www.huanqiu.com/sports/20260127/98765432.html", "国际篮球赛事"),

        # ========== 体育/足球（10个）==========
        ("https://news.qq.com/rain/a/20260129V07KQ600", "U23国足创历史"),
        ("https://sports.sina.com.cn/g/2026-01-30/doc-inhizmtt0934265.shtml", "英超积分榜形势"),
        ("https://news.qq.com/rain/a/20260127A0HJKLMN00", "西甲联赛争冠形势"),
        ("https://sports.sina.com.cn/g/2026-01-26/doc-inhizuva0934265.shtml", "意甲联赛综述"),
        ("https://news.qq.com/rain/a/20260125A03ZXC900", "法甲联赛最新赛果"),
        ("https://www.163.com/sports/20260130/A123456789.html", "德甲转会市场"),
        ("https://sports.ifeng.com/soccer/20260129/234567.shtml", "欧冠赛事前瞻"),
        ("https://www.people.com.cn/sports/20260128/n2/23456789.shtml", "中超联赛动态"),
        ("https://www.xinhuanet.com/sports/20260127/a_23456789.htm", "足球青训发展"),
        ("https://www.chinanews.com.cn/ty/20260126/t23456789.shtml", "女足赛事报道"),

        # ========== 体育/综合（8个）==========
        ("https://www.sohu.com/a/977900739_121106854", "2025年国际十大体育新闻"),
        ("https://sports.sina.com.cn/s/2026-01-30/doc-inhizmtw0934265.shtml", "网球大满贯赛事预告"),
        ("https://news.qq.com/rain/a/20260128A03ABC100", "高尔夫世界排名更新"),
        ("https://sports.sina.com.cn/o/2026-01-27/doc-inhizvqx0934265.shtml", "乒乓球世锦赛备战"),
        ("https://www.163.com/sports/20260130/A345678901.html", "F1赛车新赛季"),
        ("https://sports.ifeng.com/others/20260129/456789.shtml", "斯诺克锦标赛"),
        ("https://www.chinanews.com.cn/ty/20260128/t34567890.shtml", "田径世锦赛备战"),
        ("https://www.huanqiu.com/sports/20260127/34567890.html", "冬奥会筹备进展"),

        # ========== 财经新闻（12个）==========
        ("https://news.qq.com/rain/a/20260130A0BCDEF00", "宏观经济数据发布"),
        ("https://finance.sina.com.cn/stock/2026-01-30/doc-inhizmvn0934265.shtml", "科技股投资机会"),
        ("https://news.qq.com/rain/a/20260129A0DEFGH00", "贵金属价格波动"),
        ("https://finance.sina.com.cn/money/2026-01-29/doc-inhizmuo0934265.shtml", "房地产政策调整"),
        ("https://news.qq.com/rain/a/20260128A01JKLM200", "银行业监管新规"),
        ("https://www.163.com/money/20260130/A456789012.html", "A股市场分析"),
        ("https://finance.ifeng.com/20260129/567890.shtml", "基金市场动态"),
        ("https://www.people.com.cn/finance/20260128/n3/45678901.shtml", "货币政策解读"),
        ("https://www.xinhuanet.com/fortune/20260127/a_45678901.htm", "金融科技发展"),
        ("https://www.chinanews.com.cn/cj/20260126/t45678901.shtml", "消费市场数据"),
        ("https://www.huanqiu.com/finance/20260125/45678901.html", "国际贸易走势"),
        ("https://www.cctv.com/finance/20260124/A123456789.html", "经济政策解读"),

        # ========== 汽车新闻（10个）==========
        ("https://auto.sina.com.cn/news/2026-01-30/doc-inhiznav0934265.shtml", "新车发布预告"),
        ("https://news.qq.com/rain/a/20260127A02UVXY00", "豪华品牌销量排行"),
        ("https://auto.sina.com.cn/roll/2026-01-29/doc-inhiznbw0934265.shtml", "SUV车型对比评测"),
        ("https://news.qq.com/rain/a/20260126A03LMNO00", "车市价格战分析"),
        ("https://auto.sina.com.cn/news/2026-01-25/doc-inhiznvy0934265.shtml", "混动车型推荐"),
        ("https://www.163.com/auto/20260130/A567890123.html", "电动汽车续航测试"),
        ("https://auto.ifeng.com/20260129/678901.shtml", "智能驾驶技术"),
        ("https://www.people.com.cn/auto/20260128/n4/56789012.shtml", "新能源汽车政策"),
        ("https://www.chinanews.com.cn/auto/20260127/t56789012.shtml", "汽车销量数据"),
        ("https://www.huanqiu.com/auto/20260126/56789012.html", "豪车品牌对比"),

        # ========== 娱乐新闻（10个）==========
        ("https://ent.sina.com.cn/movie/2026-01-30/doc-inhizo0934265.shtml", "春节档电影预售"),
        ("https://ent.sina.com.cn/s/m/2026-01-29/doc-inhiznz0934265.shtml", "明星动态汇总"),
        ("https://news.qq.com/rain/a/20260128A04XYZA00", "音乐节演出阵容"),
        ("https://ent.sina.com.cn/tv/2026-01-27/doc-inhiznsq0934265.shtml", "网络综艺发展趋势"),
        ("https://ent.163.com/20260130/A678901234.html", "春节档电影票房"),
        ("https://ent.ifeng.com/20260129/789012.shtml", "热门电视剧排行"),
        ("https://www.people.com.cn/ent/20260128/n5/67890123.shtml", "音乐综艺节目"),
        ("https://ent.chinanews.com.cn/20260127/t67890123.shtml", "明星演唱会动态"),
        ("https://www.huanqiu.com/cul/20260126/67890123.html", "国产动画电影"),
        ("https://www.cctv.com/ent/20260125/A678901234.html", "综艺节目收视"),

        # ========== 国际新闻（10个）==========
        ("https://news.qq.com/rain/a/20260130A01XYZ200", "中美关系新动向"),
        ("https://news.qq.com/rain/a/20260129A02ZAQY00", "亚太经济合作动态"),
        ("https://world.sina.com.cn/2026-01-30/doc-inhiznxr0934265.shtml", "联合国重要决议"),
        ("https://news.qq.com/rain/a/20260128A03BCDE00", "全球气候谈判进展"),
        ("https://www.163.com/world/20260130/A789012345.html", "欧洲政治局势"),
        ("https://news.ifeng.com/world/20260129/890123.shtml", "中东和平进程"),
        ("https://www.people.com.cn/world/20260128/n6/78901234.shtml", "亚太地区合作"),
        ("https://www.xinhuanet.com/world/20260127/a_78901234.htm", "国际热点事件"),
        ("https://www.chinanews.com.cn/gj/20260126/t78901234.shtml", "全球气候变化"),
        ("https://www.huanqiu.com/world/20260125/78901234.html", "国际组织动态"),
    ]

    # 是否保存测试结果到文件
    save_result = True

    # 输出文件路径
    output_file = Path("./test_data/image_extraction_test_results.json")

    # 控制台显示的URL最大长度
    max_display_length = 70

    # 是否下载提取到的图片
    download_images = True

    # 图片保存目录（为None时使用下载器默认目录）
    image_save_dir = Path("./test_data/downloaded_images")

    # ==================== 执行测试 ====================
    asyncio.run(
        run_test_suite(
            test_urls,
            save_result=save_result,
            output_file=output_file,
            max_display_length=max_display_length,
            download_images=download_images,
            image_save_dir=image_save_dir,
        )
    )
