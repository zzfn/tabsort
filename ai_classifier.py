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
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/zzfn/tabsort",
                "X-Title": "TabSort"
            }
        )

        self.model = os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')

        # 构建分类提示词
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个专业的书签分类助手。请根据书签的标题和URL，智能生成合适的分类。

核心规则：
1. **域名一致性**：同一个域名的所有书签必须使用完全相同的分类（包括主分类和子分类）
   - 例如：所有 github.com 都应该归到 {"main": "技术开发", "sub": "代码仓库"}
   - 禁止同一域名分散在不同的分类中

2. **分类粒度**（重要）：
   - 主分类：控制在8-15个，涵盖主要领域
   - 子分类：当某类书签≥3个时才创建子分类
   - **禁止为单个或2个书签创建独立的主分类**，这类书签应该合并到相关的大类中
   - 例如：只有1个加密货币书签时，应归入 {"main": "金融投资", "sub": "数字货币"}，而不是创建独立的"加密货币"主分类

3. **层级关系与合并规则**（重要）：
   - 主分类应该是宽泛的领域概念，子分类用于细化
   - **避免创建语义重叠的主分类**，优先使用子分类来区分
   - 例如：
     ✅ 正确：{"main": "金融投资", "sub": "数字货币"}
     ✅ 正确：{"main": "金融投资", "sub": "股票基金"}
     ❌ 错误：同时存在 {"main": "数字货币"} 和 {"main": "金融投资"}
     ✅ 正确：{"main": "技术开发", "sub": "前端开发"}
     ❌ 错误：同时存在 {"main": "前端开发"} 和 {"main": "技术开发"}
   - 如果概念A属于概念B的一部分，则A应作为B的子分类，而非独立主分类

4. **分类命名**：
   - 使用简洁清晰的中文名称
   - 推荐的主分类参考：技术开发、设计资源、工作相关、学习资料、AI、工具软件、金融投资、视频娱乐、新闻资讯、社交平台
   - 子分类根据具体内容细化

5. **完整性**：必须为每个书签返回分类结果，不能遗漏任何书签

常见域名参考：
- github.com, stackoverflow.com → 技术开发 / 代码仓库
- juejin.cn, v2ex.com → 技术开发 / 技术社区
- binance.com, coinbase.com → 金融投资 / 数字货币
- xueqiu.com, eastmoney.com → 金融投资 / 股票基金
- feishu.cn, notion.so → 工具软件
- figma.com, dribbble.com → 设计资源
- youtube.com, bilibili.com → 视频娱乐

返回格式（sub为可选，没有子分类时填null）：
{
  "results": [
    {"no": 0, "main": "技术开发", "sub": "代码仓库"},
    {"no": 1, "main": "技术开发", "sub": "技术社区"},
    {"no": 2, "main": "设计资源", "sub": null}
  ]
}

注意：直接返回JSON，不要添加任何解释文字。
"""

    def classify(self, bookmark: Bookmark) -> Tuple[str, Optional[str]]:
        """
        使用 AI 分类单个书签
        返回: (主分类, 子分类)
        """
        user_message = f"""请分类以下书签：

标题: {bookmark.title}
URL: {bookmark.url}

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
                    "no": batch_start + idx,
                    "title": bm.title,
                    "url": bm.url
                })

            user_message = f"""请分类以下 {len(batch)} 个书签，返回JSON格式：

{json.dumps(bookmarks_data, ensure_ascii=False, indent=2)}

请返回格式（sub为可选，没有子分类时填null）：
{{
  "results": [
    {{"no": 0, "main": "主分类", "sub": "子分类"}},
    {{"no": 1, "main": "主分类", "sub": null}},
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

                # 解析 JSON
                data = json.loads(result_text)
                results = data.get('results', [])

                # 检查返回数量
                if len(results) != len(batch):
                    print(f"\n   ⚠️  AI返回数量不一致: 期望{len(batch)}个，实际{len(results)}个，未分类的将归入'未分类'")

                # 记录已处理的索引
                processed_indices = set()

                # 处理AI返回的结果
                for result in results:
                    idx = result.get('no', 0)
                    batch_idx = idx - batch_start

                    if batch_idx < 0 or batch_idx >= len(batch):
                        print(f"\n   ⚠️  索引越界: {idx}，跳过")
                        continue

                    bookmark = batch[batch_idx]
                    main_category = result.get('main', DEFAULT_CATEGORY)
                    sub_category = result.get('sub')

                    # AI自由生成分类，不再验证
                    key = (main_category, sub_category)
                    if key not in classified:
                        classified[key] = []
                    classified[key].append(bookmark)
                    processed_indices.add(batch_idx)

                # 处理未被AI分类的书签，归入"未分类"
                missing_count = len(batch) - len(processed_indices)
                if missing_count > 0:
                    print(f"\n   📌 有 {missing_count} 个书签未分类，归入'未分类'")
                    for i, bookmark in enumerate(batch):
                        if i not in processed_indices:
                            key = ("未分类", None)
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
