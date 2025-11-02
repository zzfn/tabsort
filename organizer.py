"""书签组织器"""
from typing import List, Dict
from dataclasses import dataclass
from parser import Bookmark
from config import MIN_CATEGORY_SIZE


@dataclass
class Folder:
    """文件夹数据类"""
    name: str
    bookmarks: List[Bookmark]
    subfolders: List['Folder']

    def __init__(self, name: str):
        self.name = name
        self.bookmarks = []
        self.subfolders = []

    def add_bookmark(self, bookmark: Bookmark):
        """添加书签"""
        self.bookmarks.append(bookmark)

    def add_subfolder(self, folder: 'Folder'):
        """添加子文件夹"""
        self.subfolders.append(folder)

    def get_total_count(self) -> int:
        """获取总书签数（包括子文件夹）"""
        count = len(self.bookmarks)
        for subfolder in self.subfolders:
            count += subfolder.get_total_count()
        return count

    def sort_bookmarks(self, by='title'):
        """排序书签"""
        if by == 'title':
            self.bookmarks.sort(key=lambda x: x.title.lower())
        elif by == 'domain':
            self.bookmarks.sort(key=lambda x: (x.domain or '', x.title.lower()))

        # 递归排序子文件夹
        for subfolder in self.subfolders:
            subfolder.sort_bookmarks(by)

    def sort_folders(self):
        """排序文件夹（按名称）"""
        self.subfolders.sort(key=lambda x: x.name)

        # 递归排序子文件夹
        for subfolder in self.subfolders:
            subfolder.sort_folders()


class BookmarkOrganizer:
    """书签组织器"""

    def __init__(self, classified_bookmarks: dict):
        """
        初始化
        :param classified_bookmarks: {(主分类, 子分类): [书签列表]}
        """
        self.classified_bookmarks = classified_bookmarks
        self.root = Folder("书签栏")

    def organize(self) -> Folder:
        """
        组织书签为文件夹结构
        """
        # 按主分类组织
        category_folders = {}

        for (category, subcategory), bookmarks in self.classified_bookmarks.items():
            # 创建或获取主分类文件夹
            if category not in category_folders:
                category_folders[category] = Folder(category)

            main_folder = category_folders[category]

            # 如果有子分类
            if subcategory:
                # 查找或创建子分类文件夹
                sub_folder = None
                for sf in main_folder.subfolders:
                    if sf.name == subcategory:
                        sub_folder = sf
                        break

                if not sub_folder:
                    sub_folder = Folder(subcategory)
                    main_folder.add_subfolder(sub_folder)

                # 添加书签到子分类
                for bookmark in bookmarks:
                    sub_folder.add_bookmark(bookmark)
            else:
                # 直接添加到主分类
                for bookmark in bookmarks:
                    main_folder.add_bookmark(bookmark)

        # 优化分类结构（合并小分类）
        self._optimize_structure(category_folders)

        # 添加所有主分类到根目录
        for folder in category_folders.values():
            self.root.add_subfolder(folder)

        # 排序
        self.root.sort_bookmarks(by='domain')
        self.root.sort_folders()

        return self.root

    def _optimize_structure(self, category_folders: Dict[str, Folder]):
        """
        优化文件夹结构
        - 如果子分类书签数量太少，合并到主分类
        - 如果只有一个子分类，直接合并内容（平铺）
        """
        for category_name, folder in category_folders.items():
            if not folder.subfolders:
                continue

            # 优化1：如果只有一个子分类，直接合并内容（平铺）
            if len(folder.subfolders) == 1:
                # 直接将唯一子分类的内容合并到父分类
                subfolder = folder.subfolders[0]
                folder.bookmarks.extend(subfolder.bookmarks)
                folder.subfolders.remove(subfolder)
                continue

            # 优化2：检查每个子文件夹，如果数量太少则合并到主分类
            to_merge = []
            for subfolder in folder.subfolders:
                if len(subfolder.bookmarks) < MIN_CATEGORY_SIZE:
                    to_merge.append(subfolder)

            # 合并小分类到主分类
            for subfolder in to_merge:
                folder.bookmarks.extend(subfolder.bookmarks)
                folder.subfolders.remove(subfolder)

    def print_structure(self, folder: Folder = None, indent: int = 0):
        """
        打印文件夹结构（用于调试）
        """
        if folder is None:
            folder = self.root

        prefix = "  " * indent
        print(f"{prefix}📁 {folder.name} ({folder.get_total_count()})")

        # 打印书签
        if folder.bookmarks:
            for bookmark in folder.bookmarks[:3]:  # 只显示前3个
                print(f"{prefix}  🔖 {bookmark.title[:50]}")
            if len(folder.bookmarks) > 3:
                print(f"{prefix}  ... 还有 {len(folder.bookmarks) - 3} 个书签")

        # 递归打印子文件夹
        for subfolder in folder.subfolders:
            self.print_structure(subfolder, indent + 1)
