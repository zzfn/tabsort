"""
书签智能整理工具
功能：
1. 解析Chrome书签HTML文件
2. 智能分类书签
3. 生成整理后的HTML文件
"""

import os
import glob
from datetime import datetime
from pick import pick
from parser import BookmarkParser
from classifier import BookmarkClassifier
from organizer import BookmarkOrganizer
from generator import BookmarkHTMLGenerator


def select_html_file():
    """列出当前目录的HTML文件供用户选择"""
    html_files = glob.glob("*.html")

    if not html_files:
        print("❌ 当前目录下没有找到 HTML 文件")
        print("💡 请先导出 Chrome 书签到当前目录")
        return None

    # 准备选项列表（文件名 + 详细信息）
    options = []
    for file in html_files:
        file_size = os.path.getsize(file) / 1024  # KB
        mod_time = datetime.fromtimestamp(os.path.getmtime(file))
        # 格式化显示
        display = f"{file:<30} | {file_size:>8.1f} KB | {mod_time.strftime('%Y-%m-%d %H:%M:%S')}"
        options.append((display, file))

    try:
        title = "\n📋 请使用 ↑↓ 方向键选择要整理的书签文件，按 Enter 确认:\n"
        # 使用 pick 进行交互式选择
        selected, index = pick([opt[0] for opt in options], title, indicator="=>")

        # 返回实际的文件名
        return options[index][1]

    except KeyboardInterrupt:
        print("\n\n👋 已取消")
        return None


def main():
    print("=" * 60)
    print("Chrome 书签智能整理工具")
    print("=" * 60)

    # 选择输入文件
    input_file = select_html_file()
    if not input_file:
        return

    # 生成输出文件名（只用时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{timestamp}.html"

    # 1. 解析书签
    print(f"\n📖 正在解析书签文件: {input_file}")
    parser = BookmarkParser(input_file)
    bookmarks = parser.parse()

    # 去重
    unique_bookmarks, duplicates = parser.get_unique_bookmarks()

    print(f"✅ 解析完成！")
    print(f"   总书签数: {len(bookmarks)}")
    print(f"   去重后: {len(unique_bookmarks)}")

    if duplicates:
        print(f"   删除重复: {len(duplicates)} 个")
        print(f"\n🗑️  已删除的重复书签:")
        print("-" * 60)
        for dup in duplicates:
            title = dup.title[:60] if len(dup.title) > 60 else dup.title
            print(f"   • {title}")
            print(f"     URL: {dup.url}")
            print()

    # 2. 智能分类
    print(f"\n🤖 正在智能分类...")
    classifier = BookmarkClassifier()
    classified = classifier.classify_batch(unique_bookmarks)

    # 获取分类统计
    stats = classifier.get_category_stats(classified)

    print(f"✅ 分类完成！")
    print(f"\n📊 分类统计:")
    print("-" * 60)

    # 按书签数量排序显示
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True)

    for category, info in sorted_stats:
        print(f"\n📁 {category} ({info['total']} 个)")
        if info['subcategories']:
            for subcat, count in sorted(info['subcategories'].items(),
                                         key=lambda x: x[1], reverse=True):
                print(f"   └─ {subcat}: {count}")

    # 3. 组织书签结构
    print(f"\n📂 正在组织文件夹结构...")
    organizer = BookmarkOrganizer(classified)
    root = organizer.organize()

    print(f"✅ 组织完成！")

    # 4. 生成HTML
    print(f"\n💾 正在生成HTML文件: {output_file}")
    generator = BookmarkHTMLGenerator(root)

    # 显示预览
    print(generator.get_preview())

    # 生成文件
    generator.generate(output_file)

    print(f"\n✅ 生成完成！")
    print(f"\n📄 整理后的书签已保存到: {output_file}")
    print(f"\n💡 导入方法:")
    print(f"   1. 打开 Chrome 浏览器")
    print(f"   2. 按 Ctrl+Shift+O (或 Cmd+Shift+O) 打开书签管理器")
    print(f"   3. 点击右上角的 '...' 菜单")
    print(f"   4. 选择 '导入书签'")
    print(f"   5. 选择文件: {output_file}")
    print(f"\n" + "=" * 60)


if __name__ == "__main__":
    main()
