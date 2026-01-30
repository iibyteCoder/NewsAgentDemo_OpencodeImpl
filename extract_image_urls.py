import json

# 从数据库结果中提取所有图片URL
news_data = {
    "results": [
        {
            "title": "上海人工智能实验室发布书生·天际LandMark三维实景大模型",
            "image_urls": '["https://inews.gtimg.com/newsapp_bt/0/1012205723968_6694/0"]',
        },
        {
            "title": "上海 AI 实验室发布书生・浦语大模型",
            "image_urls": '["https://inews.gtimg.com/newsapp_bt/0/1012205723968_6694/0"]',
        },
        {
            "title": "会看图、看视频，还精通161种语言",
            "image_urls": '["https://inews.gtimg.com/newsapp_bt/0/1012205723968_6694/0"]',
        },
        {
            "title": "AGI上海方案全球关注",
            "image_urls": '["https://q4.itc.cn/c_lfill,w_180,h_120,g_face/images01/20260130/be10305fd5c9486585e6b642034b8a15.jpeg", "https://q8.itc.cn/q_70,c_lfill,w_290,h_174,g_face/images03/20260129/620477e022894484aed9d09ff344e3fa.jpeg", "https://q5.itc.cn/q_70/images03/20260130/52f1fca434e44d12a3739d3af85d9ca6.jpeg", "https://q0.itc.cn/q_70,c_lfill,w_290,h_174,g_face/images03/20260130/19ada11fa3094c74b5b4103ebee92221.png", "https://q8.itc.cn/q_70,c_lfill,w_290,h_174,g_face/images01/20260129/7dafd1a5b9cd4868a119af69db25626a.png"]',
        },
        {
            "title": "ChartVerse",
            "image_urls": '["https://inews.gtimg.com/newsapp_bt/0/1012205723968_6694/0"]',
        },
        {
            "title": "AAAI 2026首次落地新加坡",
            "image_urls": '["https://inews.gtimg.com/newsapp_bt/0/1012205723968_6694/0"]',
        },
        {
            "title": "周伯文：缺乏专业推理能力",
            "image_urls": '["https://inews.gtimg.com/newsapp_bt/0/1012205723968_6694/0", "https://mat1.gtimg.com/qqcdn/tupload/1686551149573.png"]',
        },
        {
            "title": "AGI上海方案全球关注（文汇报/上观新闻）",
            "image_urls": '["https://t11.baidu.com/it/u=1231248859,287831370&fm=30&app=106&f=JPEG?w=533&h=300&s=5BE69856DC44DF0142FCF9FA03000035"]',
        },
    ]
}

# 提取所有图片URL并去重
all_image_urls = []
url_to_news = {}  # 记录URL到新闻标题的映射
for news in news_data["results"]:
    try:
        image_urls = json.loads(news["image_urls"])
        for url in image_urls:
            all_image_urls.append(url)
            if url not in url_to_news:
                url_to_news[url] = []
            url_to_news[url].append(news["title"])
    except Exception as e:
        print(f"解析图片URL失败 ({news['title']}): {e}")

# 去重
unique_urls = list(set(all_image_urls))

# 输出结果
print(f"Original images: {len(all_image_urls)}")
print(f"Unique images: {len(unique_urls)}")
print("\nUnique image URLs:")
for i, url in enumerate(unique_urls, 1):
    print(f"{i}. {url}")
    # print(f'   Source: {", ".join(url_to_news[url][:2])}')
    print()

# 输出JSON格式方便下载
print("\nJSON format:")
print(json.dumps(unique_urls, indent=2, ensure_ascii=False))

# 保存到文件
with open("image_urls.json", "w", encoding="utf-8") as f:
    json.dump(unique_urls, f, indent=2, ensure_ascii=False)
print("\nSaved to image_urls.json")
