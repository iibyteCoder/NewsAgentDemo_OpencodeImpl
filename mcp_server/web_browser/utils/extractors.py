"""
智能文章内容提取器

基于 readability-like 算法实现：
- 分析文本密度
- 识别正文容器
- 过滤广告、导航等无关内容
- 智能提取标题和正文
"""

from loguru import logger


async def extract_article_content(page, url: str = "") -> dict:
    """智能提取文章内容（基于 readability-like 算法）

    Args:
        page: Playwright页面对象
        url: 页面URL（用于日志）

    Returns:
        包含 title, content, html_content 的字典
    """
    logger.info("   🔍 使用智能算法提取文章内容")

    result = await page.evaluate(
        """() => {
        // ========== 配置参数 ==========
        const MIN_TEXT_LENGTH = 20;      // 最小文本长度
        const MIN_PARAGRAPHS = 2;        // 最小段落数
        const MAX_LINK_DENSITY = 0.3;    // 最大链接密度
        const MIN_SCORE = 20;            // 最小得分

        // ========== 辅助函数 ==========

        // 获取元素的纯文本长度
        function getTextLength(element) {
            const text = element.textContent || '';
            return text.trim().length;
        }

        // 获取元素的链接密度（链接文本占总文本的比例）
        function getLinkDensity(element) {
            const textLength = getTextLength(element);
            if (textLength === 0) return 0;

            const links = element.getElementsByTagName('a');
            let linkTextLength = 0;

            for (const link of links) {
                linkTextLength += (link.textContent || '').trim().length;
            }

            return linkTextLength / textLength;
        }

        // 计算元素得分（基于文本密度、段落数量等）
        function calculateScore(element) {
            let score = 0;

            // 1. 文本长度得分
            const textLength = getTextLength(element);
            if (textLength > 0) {
                score += Math.log(textLength + 1);
            }

            // 2. 段落数量得分
            const paragraphs = element.getElementsByTagName('p');
            const validParagraphs = Array.from(paragraphs).filter(p =>
                getTextLength(p) >= MIN_TEXT_LENGTH
            );

            score += validParagraphs.length * 5;

            // 3. 标题元素加分
            const headings = element.querySelectorAll('h1, h2, h3, h4, h5, h6');
            score += headings.length * 3;

            // 4. 图片加分（但不是图片为主的元素）
            const images = element.getElementsByTagName('img');
            const textToImageRatio = textLength / (images.length + 1);
            if (textToImageRatio > 50) {
                score += images.length * 2;
            }

            // 5. 列表加分
            const lists = element.querySelectorAll('ul, ol');
            score += lists.length * 2;

            // 6. 链接密度惩罚
            const linkDensity = getLinkDensity(element);
            if (linkDensity > MAX_LINK_DENSITY) {
                score *= (1 - linkDensity);
            }

            // 7. 类名/ID名加分或惩罚
            const className = element.className || '';
            const id = element.id || '';
            const classAndId = (className + ' ' + id).toLowerCase();

            // 正面关键词（表明是正文）
            const positiveKeywords = [
                'article', 'content', 'post', 'text', 'body', 'main',
                'story', 'entry', 'blog', 'news', 'detail', 'excerpt'
            ];

            // 负面关键词（表明不是正文）
            const negativeKeywords = [
                'comment', 'footer', 'header', 'nav', 'sidebar', 'ad',
                'advertisement', 'related', 'recommend', 'share', 'social',
                'menu', 'breadcrumb', 'pagination', 'tag', 'category'
            ];

            for (const keyword of positiveKeywords) {
                if (classAndId.includes(keyword)) {
                    score += 25;
                    break;
                }
            }

            for (const keyword of negativeKeywords) {
                if (classAndId.includes(keyword)) {
                    score -= 25;
                    break;
                }
            }

            return score;
        }

        // ========== 主提取逻辑 ==========

        // 1. 提取标题
        let title = '';
        const titleSelectors = [
            'h1',
            '.article-title',
            '.news-title',
            '.post-title',
            '.entry-title',
            '[class*="title"]',
            '#title',
            'title'
        ];

        for (const selector of titleSelectors) {
            const elem = document.querySelector(selector);
            if (elem) {
                const text = (elem.textContent || '').trim();
                if (text.length > 5) {
                    title = text;
                    break;
                }
            }
        }

        // 2. 移除不需要的元素
        const unwantedSelectors = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            'iframe', 'noscript', 'meta', 'link',
            '[class*="ad"]', '[class*="advertisement"]',
            '[class*="sidebar"]', '[class*="comment"]',
            '[class*="share"]', '[class*="social"]',
            '[id*="ad"]', '[id*="advertisement"]',
            '.related', '.recommend', '.menu', '.breadcrumb'
        ];

        // 克隆body以避免修改原始DOM
        const bodyClone = document.body.cloneNode(true);

        // 移除不需要的元素
        unwantedSelectors.forEach(selector => {
            const elements = bodyClone.querySelectorAll(selector);
            elements.forEach(el => el.remove());
        });

        // 3. 找到候选容器
        const candidates = [];

        // 查找所有可能的容器
        const candidateSelectors = [
            'article',
            '[role="article"]',
            '.article-content',
            '.article-body',
            '.news-content',
            '.post-content',
            '.entry-content',
            '.content',
            '[class*="content"]',
            '#content',
            'main',
            '[role="main"]',
            '.main',
            '.post-body',
            '.detail-content',
            '.text-content'
        ];

        for (const selector of candidateSelectors) {
            const elements = bodyClone.querySelectorAll(selector);
            for (const elem of elements) {
                const textLength = getTextLength(elem);
                if (textLength >= 100) {  // 至少100个字符
                    const score = calculateScore(elem);
                    candidates.push({
                        element: elem,
                        score: score,
                        textLength: textLength
                    });
                }
            }
        }

        // 如果没有找到候选，考虑body的直接子元素
        if (candidates.length === 0) {
            for (const elem of bodyClone.children) {
                const textLength = getTextLength(elem);
                if (textLength >= 200) {
                    const score = calculateScore(elem);
                    candidates.push({
                        element: elem,
                        score: score,
                        textLength: textLength
                    });
                }
            }
        }

        // 4. 选择得分最高的容器
        if (candidates.length > 0) {
            candidates.sort((a, b) => b.score - a.score);
            const bestCandidate = candidates[0].element;

            // 5. 从选中的容器中提取段落
            const paragraphs = bestCandidate.querySelectorAll('p, h1, h2, h3, h4, h5, h6');
            const contentParts = [];

            for (const p of paragraphs) {
                const text = (p.textContent || '').trim();
                if (text.length >= MIN_TEXT_LENGTH) {
                    // 过滤掉明显的广告/推荐文本
                    if (!text.includes('点击查看') &&
                        !text.includes('关注我们') &&
                        !text.includes('扫码') &&
                        !text.includes('转载请注明') &&
                        !text.match(/^[\\d\\s]+$/) &&
                        text.length < 500) {  // 避免过长的单个段落
                        contentParts.push(text);
                    }
                }
            }

            // 如果段落数太少，尝试提取所有文本节点
            if (contentParts.length < MIN_PARAGRAPHS) {
                const walker = document.createTreeWalker(
                    bestCandidate,
                    NodeFilter.SHOW_TEXT,
                    null
                );

                let node;
                const texts = [];
                while (node = walker.nextNode()) {
                    const text = node.textContent.trim();
                    if (text.length >= MIN_TEXT_LENGTH) {
                        texts.push(text);
                    }
                }

                if (texts.length >= MIN_PARAGRAPHS) {
                    return {
                        title: title,
                        content: texts.slice(0, 30).join('\\n\\n'),
                        htmlContent: bestCandidate.innerHTML,
                        method: 'text-nodes',
                        score: candidates[0].score
                    };
                }
            }

            if (contentParts.length >= MIN_PARAGRAPHS) {
                return {
                    title: title,
                    content: contentParts.slice(0, 30).join('\\n\\n'),
                    htmlContent: bestCandidate.innerHTML,
                    method: 'paragraphs',
                    score: candidates[0].score
                };
            }
        }

        // 5. 最后的备用方案：提取body中的所有段落
        const allParagraphs = document.querySelectorAll('body p, body h1, body h2, body h3, body h4, body h5, body h6');
        const fallbackParts = [];

        for (const p of allParagraphs) {
            const text = (p.textContent || '').trim();
            if (text.length >= MIN_TEXT_LENGTH && text.length < 500) {
                if (!text.includes('点击') &&
                    !text.includes('关注') &&
                    !text.includes('免责声明')) {
                    fallbackParts.push(text);
                }
            }
        }

        return {
            title: title,
            content: fallbackParts.slice(0, 30).join('\\n\\n'),
            htmlContent: document.body.innerHTML,
            method: 'fallback',
            score: 0
        };
    }"""
    )

    if result and result.get("content") and len(result.get("content", "")) > 100:
        logger.info(
            f"   ✅ 智能算法提取成功 (方法: {result.get('method')}, 得分: {result.get('score', 0):.1f})"
        )
        return {
            "title": result.get("title", ""),
            "content": result.get("content", ""),
            "html_content": result.get("htmlContent", ""),
        }
    else:
        logger.warning("   ⚠️ 智能算法提取内容过少，将使用备用方案")
        return {"title": "", "content": "", "html_content": ""}


async def extract_title(page) -> str:
    """智能提取文章标题

    Args:
        page: Playwright页面对象

    Returns:
        标题文本
    """
    title = await page.evaluate(
        """() => {
        // 尝试多种选择器
        const selectors = [
            'h1',
            '.article-title',
            '.news-title',
            '.post-title',
            '.entry-title',
            '[class*="title"]',
            '#title',
            'title'
        ];

        for (const selector of selectors) {
            const elem = document.querySelector(selector);
            if (elem) {
                const text = (elem.textContent || '').trim();
                if (text.length > 5 && text.length < 200) {
                    return text;
                }
            }
        }

        // 如果都没找到，返回页面标题
        return document.title || '';
    }"""
    )

    return title if title else ""
