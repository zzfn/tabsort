"""书签解析器"""
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class Bookmark:
    """书签数据类"""
    url: str
    title: str
    add_date: Optional[str] = None
    icon: Optional[str] = None
    domain: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.url and not self.domain:
            self.domain = self._extract_domain(self.url)

    @staticmethod
    def _extract_domain(url: str) -> str:
        """提取域名"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # 移除 www. 前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""


class BookmarkParser:
    """书签解析器"""

    def __init__(self, html_file: str):
        self.html_file = html_file
        self.bookmarks: List[Bookmark] = []

    def parse(self) -> List[Bookmark]:
        """解析书签文件"""
        with open(self.html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # 查找所有的书签链接
        links = soup.find_all('a')

        for link in links:
            url = link.get('href')
            if not url:
                continue

            title = link.get_text(strip=True)
            add_date = link.get('add_date')
            icon = link.get('icon')

            bookmark = Bookmark(
                url=url,
                title=title,
                add_date=add_date,
                icon=icon
            )

            self.bookmarks.append(bookmark)

        return self.bookmarks

    def get_unique_bookmarks(self) -> tuple[List[Bookmark], List[Bookmark]]:
        """
        获取去重后的书签（基于URL）
        返回: (唯一书签列表, 重复书签列表)
        """
        seen = {}  # url -> bookmark
        unique = []
        duplicates = []

        for bookmark in self.bookmarks:
            if bookmark.url not in seen:
                seen[bookmark.url] = bookmark
                unique.append(bookmark)
            else:
                duplicates.append(bookmark)

        return unique, duplicates

    def find_hash_only_duplicates(self) -> List[tuple[str, List[Bookmark]]]:
        """
        查找只有hash不同的重复书签
        返回: [(基础URL, [书签列表])] - 只返回有多个书签的组
        """
        from urllib.parse import urlparse, urlunparse

        # 移除URL的hash部分
        def remove_hash(url: str) -> str:
            parsed = urlparse(url)
            # 将hash部分设为空，重新组合URL
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                ''  # 移除fragment(hash)
            ))

        # 按无hash的URL分组
        url_groups = {}
        for bookmark in self.bookmarks:
            base_url = remove_hash(bookmark.url)
            if base_url not in url_groups:
                url_groups[base_url] = []
            url_groups[base_url].append(bookmark)

        # 只返回有多个书签的组（即有重复的）
        duplicates = [(url, bookmarks) for url, bookmarks in url_groups.items()
                      if len(bookmarks) > 1]

        # 按重复数量排序
        duplicates.sort(key=lambda x: len(x[1]), reverse=True)

        return duplicates

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self.bookmarks)
        unique_bookmarks, _ = self.get_unique_bookmarks()
        unique = len(unique_bookmarks)

        domains = {}
        for bookmark in self.bookmarks:
            if bookmark.domain:
                domains[bookmark.domain] = domains.get(bookmark.domain, 0) + 1

        return {
            'total': total,
            'unique': unique,
            'duplicates': total - unique,
            'domains_count': len(domains),
            'domains': domains
        }
