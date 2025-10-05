"""HTML生成器"""
from typing import TextIO
from organizer import Folder
import time
import html


class BookmarkHTMLGenerator:
    """Chrome书签HTML生成器"""

    def __init__(self, root_folder: Folder):
        self.root = root_folder

    def generate(self, output_file: str):
        """生成HTML文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            self._write_header(f)
            self._write_folder(f, self.root, is_root=True)
            self._write_footer(f)

    def _write_header(self, f: TextIO):
        """写入HTML头部"""
        f.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')
        f.write('<!-- This is an automatically generated file.\n')
        f.write('     It will be read and overwritten.\n')
        f.write('     DO NOT EDIT! -->\n')
        f.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
        f.write('<TITLE>Bookmarks</TITLE>\n')
        f.write('<H1>Bookmarks</H1>\n')
        f.write('<DL><p>\n')

    def _write_footer(self, f: TextIO):
        """写入HTML尾部"""
        f.write('</DL><p>\n')

    def _write_folder(self, f: TextIO, folder: Folder, indent: int = 1, is_root: bool = False):
        """
        写入文件夹及其内容
        """
        spaces = '    ' * indent
        timestamp = str(int(time.time()))

        if is_root:
            # 根目录（书签栏）
            f.write(f'{spaces}<DT><H3 ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}" '
                    f'PERSONAL_TOOLBAR_FOLDER="true">{html.escape(folder.name)}</H3>\n')
        else:
            # 普通文件夹
            f.write(f'{spaces}<DT><H3 ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}">'
                    f'{html.escape(folder.name)}</H3>\n')

        f.write(f'{spaces}<DL><p>\n')

        # 写入子文件夹
        for subfolder in folder.subfolders:
            self._write_folder(f, subfolder, indent + 1)

        # 写入书签
        for bookmark in folder.bookmarks:
            self._write_bookmark(f, bookmark, indent + 1)

        f.write(f'{spaces}</DL><p>\n')

    def _write_bookmark(self, f: TextIO, bookmark, indent: int):
        """写入单个书签"""
        spaces = '    ' * indent

        # 构建书签标签
        attrs = [f'HREF="{html.escape(bookmark.url)}"']

        if bookmark.add_date:
            attrs.append(f'ADD_DATE="{bookmark.add_date}"')
        else:
            attrs.append(f'ADD_DATE="{int(time.time())}"')

        if bookmark.icon:
            attrs.append(f'ICON="{html.escape(bookmark.icon)}"')

        attrs_str = ' '.join(attrs)
        title = html.escape(bookmark.title) if bookmark.title else html.escape(bookmark.url)

        f.write(f'{spaces}<DT><A {attrs_str}>{title}</A>\n')

    def get_preview(self, max_folders: int = 5) -> str:
        """
        生成预览文本
        """
        lines = []
        lines.append("=" * 60)
        lines.append("书签整理预览")
        lines.append("=" * 60)
        lines.append(f"总计: {self.root.get_total_count()} 个书签")
        lines.append(f"分类数: {len(self.root.subfolders)} 个")
        lines.append("=" * 60)
        return "\n".join(lines)
