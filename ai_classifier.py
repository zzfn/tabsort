"""AI 智能分类器"""
import os
import json
from typing import List, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv
from parser import Bookmark
from config import DEFAULT_CATEGORY

# 加载环境变量
load_dotenv()


class AIBookmarkClassifier:
    """基于 AI 的书签智能分类器"""

    def __init__(self):
        # 初始化 OpenRouter 客户端
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("请在 .env 文件中设置 OPENROUTER_API_KEY")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        self.model = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')

        # 构建分类提示词
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个专业的书签分类助手。请根据书签的标题、URL和域名，自动生成合适的分类。

分类原则：
1. 根据书签的主题和用途创建分类名称（如：技术学习、工作相关、设计资源等）
2. 为相似的书签使用相同的分类名称，保持一致性
3. 可以创建子分类使分类更精确（如：技术学习 > 前端开发）
4. 分类名称要简洁明确，使用中文
5. 常见网站域名：
   - github.com, stackoverflow.com → 技术学习
   - juejin.cn, v2ex.com, zhihu.com → 可单独子分类
   - feishu.cn → 工作相关
   - dribbble.com, behance.net → 设计资源
   - youtube.com, bilibili.com → 娱乐生活

重要：
- 直接返回JSON，不要添加任何解释或额外文字
- 确保JSON格式完整、有效
- 保持分类名称的一致性，相同类型的网站应使用相同的分类

返回格式示例：
{
  "results": [
    {"index": 0, "main": "技术学习", "sub": "代码仓库"},
    {"index": 1, "main": "技术学习", "sub": "掘金"},
    {"index": 2, "main": "资讯媒体", "sub": "知乎"},
    {"index": 3, "main": "设计资源", "sub": "设计工具"}
  ]
}
"""

    def classify(self, bookmark: Bookmark) -> Tuple[str, Optional[str]]:
        """
        使用 AI 分类单个书签
        返回: (主分类, 子分类)
        """
        user_message = f"""请分类以下书签：

标题: {bookmark.title}
URL: {bookmark.url}
域名: {bookmark.domain}

请返回 JSON 格式的分类结果。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=150,
                timeout=30.0  # 30秒超时
            )

            result_text = response.choices[0].message.content.strip()

            # 尝试解析 JSON - 改进的解析逻辑
            # 移除可能的 markdown 代码块标记
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                # 移除第一行的 ```json 和最后一行的 ```
                result_text = '\n'.join(lines[1:-1]).strip()

            # 提取第一个有效的JSON对象
            # 处理多行或带额外文本的情况
            start = result_text.find('{')
            end = result_text.find('}', start)
            if start != -1 and end != -1:
                result_text = result_text[start:end+1]

            result = json.loads(result_text)

            main_category = result.get('main', DEFAULT_CATEGORY)
            sub_category = result.get('sub')

            # 不再验证分类，AI可以自由生成分类名称
            return main_category, sub_category

        except Exception as e:
            print(f"⚠️  AI 分类失败 ({bookmark.title[:30]}...): {str(e)}")
            # 降级到默认分类
            return DEFAULT_CATEGORY, None

    def classify_batch(self, bookmarks: List[Bookmark], batch_size: int = 1000) -> dict:
        """
        批量分类书签（真正的批量，一次请求多个）
        返回: {(主分类, 子分类): [书签列表]}
        """
        classified = {}
        total = len(bookmarks)

        print(f"\n🤖 使用 AI 进行智能分类...")
        print(f"   模型: {self.model}")
        print(f"   总计: {total} 个书签")
        print(f"   批量大小: {batch_size} 个/次")

        # 分批处理
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch = bookmarks[batch_start:batch_end]

            print(f"\n   处理批次: {batch_start+1}-{batch_end}/{total}")

            # 构建批量请求
            bookmarks_data = []
            for idx, bm in enumerate(batch):
                bookmarks_data.append({
                    "index": batch_start + idx,
                    "title": bm.title,
                    "url": bm.url,
                    "domain": bm.domain
                })

            user_message = f"""请分类以下 {len(batch)} 个书签，返回JSON格式：

{json.dumps(bookmarks_data, ensure_ascii=False, indent=2)}

请返回格式：
{{
  "results": [
    {{"index": 0, "main": "主分类", "sub": "子分类或null"}},
    {{"index": 1, "main": "主分类", "sub": "子分类或null"}},
    ...
  ]
}}"""

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.3,
                    timeout=120.0,  # 增加超时时间
                    response_format={"type": "json_object"}
                )

                # 检查响应
                if not response.choices:
                    raise ValueError("API返回choices为空")

                result_text = response.choices[0].message.content

                if not result_text:
                    raise ValueError(f"API返回内容为空，finish_reason: {response.choices[0].finish_reason}")

                result_text = result_text.strip()

                # 解析 JSON - response_format 应该保证返回纯JSON
                try:
                    data = json.loads(result_text)
                except json.JSONDecodeError as je:
                    print(f"\n   ⚠️  JSON解析失败: {je}")
                    print(f"   返回内容长度: {len(result_text)}")
                    print(f"   返回内容前500字符: {result_text[:500]}")
                    print(f"   finish_reason: {response.choices[0].finish_reason}")
                    raise

                results = data.get('results', [])

                # 处理结果
                for result in results:
                    idx = result.get('index', 0)
                    if idx >= len(batch):
                        continue

                    bookmark = batch[idx - batch_start]
                    main_category = result.get('main', DEFAULT_CATEGORY)
                    sub_category = result.get('sub')

                    # AI自由生成分类，不再验证
                    key = (main_category, sub_category)
                    if key not in classified:
                        classified[key] = []
                    classified[key].append(bookmark)

            except Exception as e:
                print(f"\n   ⚠️  批次分类失败: {str(e)}")
                print(f"   降级为逐个分类...")
                # 降级处理：逐个分类这个批次
                for bookmark in batch:
                    category, subcategory = self.classify(bookmark)
                    key = (category, subcategory)
                    if key not in classified:
                        classified[key] = []
                    classified[key].append(bookmark)

        return classified

    def get_category_stats(self, classified: dict) -> dict:
        """获取分类统计"""
        stats = {}

        for (category, subcategory), bookmarks in classified.items():
            if category not in stats:
                stats[category] = {
                    'total': 0,
                    'subcategories': {}
                }

            count = len(bookmarks)
            stats[category]['total'] += count

            if subcategory:
                stats[category]['subcategories'][subcategory] = count
            else:
                stats[category]['subcategories']['未分组'] = count

        return stats
