#!/usr/bin/env python3
"""Simple script to process a news article using news-processor agent"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import required modules
from opencode import agent


async def main():
    """Process a news article using news-processor agent"""

    # News data from the prompt
    news_data = {
        "title": "中东2025之伊朗:一场战争 双重危机 冲突下的乱局与困境",
        "url": "https://baijiahao.baidu.com/s?id=1852352103126574171&wfr=spider&for=pc",
        "time": "2025年12月24日",
    }

    session_id = "20260204-ed8ff50e"
    category = "国际局势"

    # Prepare prompt for the agent
    prompt = f"""处理这条新闻：{json.dumps(news_data, ensure_ascii=False)} session_id={session_id} category={category}"""

    print(f"Calling news-processor agent with URL: {news_data['url']}")
    print(f"Session ID: {session_id}")
    print(f"Category: {category}")
    print("-" * 50)

    # Call the agent
    try:
        result = await agent("news-processor", prompt)

        print("\nAgent Result:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"Error calling agent: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
