"""智能分类器"""
from typing import List, Tuple, Optional
from parser import Bookmark
from config import CATEGORIES, DEFAULT_CATEGORY


class BookmarkClassifier:
    """书签智能分类器"""

    def __init__(self):
        self.categories = CATEGORIES

    def classify(self, bookmark: Bookmark) -> Tuple[str, Optional[str]]:
        """
        分类单个书签
        返回: (主分类, 子分类)
        """
        # 准备用于匹配的文本（小写）
        url_lower = bookmark.url.lower()
        title_lower = bookmark.title.lower()
        domain_lower = bookmark.domain.lower() if bookmark.domain else ""

        # 遍历所有分类
        for category_name, category_info in self.categories.items():
            # 检查主分类
            if self._matches_category(url_lower, title_lower, domain_lower, category_info):
                # 检查子分类
                if 'subcategories' in category_info:
                    for sub_name, sub_info in category_info['subcategories'].items():
                        if self._matches_category(url_lower, title_lower, domain_lower, sub_info):
                            return category_name, sub_name

                # 只匹配主分类
                return category_name, None

        # 未匹配到任何分类
        return DEFAULT_CATEGORY, None

    def _matches_category(self, url: str, title: str, domain: str, category_info: dict) -> bool:
        """
        检查是否匹配分类
        """
        # 检查域名匹配
        if 'domains' in category_info:
            for cat_domain in category_info['domains']:
                if cat_domain.lower() in domain:
                    return True

        # 检查关键词匹配
        if 'keywords' in category_info:
            for keyword in category_info['keywords']:
                keyword_lower = keyword.lower()
                if keyword_lower in url or keyword_lower in title or keyword_lower in domain:
                    return True

        # 检查URL模式匹配
        if 'url_patterns' in category_info:
            for pattern in category_info['url_patterns']:
                if pattern.lower() in url:
                    return True

        return False

    def classify_batch(self, bookmarks: List[Bookmark]) -> dict:
        """
        批量分类书签
        返回: {(主分类, 子分类): [书签列表]}
        """
        classified = {}

        for bookmark in bookmarks:
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
