package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type Profile struct {
	Name string
	Path string
	Size int64
}

func findProfiles() []Profile {
	chromeBase := filepath.Join(os.Getenv("HOME"), "Library/Application Support/Google/Chrome")
	entries, err := os.ReadDir(chromeBase)
	if err != nil {
		return nil
	}

	var profiles []Profile
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		name := e.Name()
		if name != "Default" && !strings.HasPrefix(name, "Profile ") {
			continue
		}
		bmPath := filepath.Join(chromeBase, name, "Bookmarks")
		info, err := os.Stat(bmPath)
		if err != nil {
			continue
		}

		displayName := name
		prefPath := filepath.Join(chromeBase, name, "Preferences")
		if data, err := os.ReadFile(prefPath); err == nil {
			var prefs struct {
				Profile struct {
					Name string `json:"name"`
				} `json:"profile"`
			}
			if json.Unmarshal(data, &prefs) == nil && prefs.Profile.Name != "" {
				displayName = prefs.Profile.Name + " (" + name + ")"
			}
		}

		profiles = append(profiles, Profile{
			Name: displayName,
			Path: bmPath,
			Size: info.Size(),
		})
	}

	// 按书签大小降序排列，最大的（主账号）排在前面
	sort.Slice(profiles, func(i, j int) bool {
		return profiles[i].Size > profiles[j].Size
	})

	return profiles
}

var stdin = bufio.NewScanner(os.Stdin)

func readLine(prompt string) string {
	fmt.Print(prompt)
	stdin.Scan()
	return strings.TrimSpace(stdin.Text())
}

func selectProfile(profiles []Profile) *Profile {
	fmt.Println("\n📋 选择 Chrome 配置文件:")
	fmt.Println(strings.Repeat("-", 60))
	for i, p := range profiles {
		fmt.Printf("  %d. %-40s %8.1f KB\n", i+1, p.Name, float64(p.Size)/1024)
	}
	fmt.Println(strings.Repeat("-", 60))

	input := readLine(fmt.Sprintf("输入序号 [1-%d，默认 1]: ", len(profiles)))
	idx := 0
	if input != "" {
		if n, err := strconv.Atoi(input); err == nil && n >= 1 && n <= len(profiles) {
			idx = n - 1
		}
	}
	return &profiles[idx]
}

func selectMode() string {
	if os.Getenv("OPENROUTER_API_KEY") == "" {
		fmt.Println("\n💡 未设置 OPENROUTER_API_KEY，使用规则分类")
		return "rules"
	}

	fmt.Println("\n🎯 选择分类模式:")
	fmt.Println("  1. 🤖 AI 智能分类 (OpenRouter)")
	fmt.Println("  2. 📏 规则分类")

	input := readLine("输入序号 [默认 1]: ")
	if input == "2" {
		return "rules"
	}
	return "ai"
}

func loadEnv() {
	data, err := os.ReadFile(".env")
	if err != nil {
		return
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		k, v, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		k = strings.TrimSpace(k)
		v = strings.TrimSpace(v)
		if os.Getenv(k) == "" {
			os.Setenv(k, v)
		}
	}
}

func printStats(classified map[CategoryKey][]Bookmark) {
	fmt.Println("\n📊 分类统计:")
	fmt.Println(strings.Repeat("-", 50))

	mainCount := make(map[string]int)
	subCount := make(map[string]map[string]int)

	for key, bms := range classified {
		mainCount[key.Main] += len(bms)
		if key.Sub != "" {
			if subCount[key.Main] == nil {
				subCount[key.Main] = make(map[string]int)
			}
			subCount[key.Main][key.Sub] += len(bms)
		}
	}

	// 按数量降序
	type entry struct{ name string; count int }
	mains := make([]entry, 0, len(mainCount))
	for k, v := range mainCount {
		mains = append(mains, entry{k, v})
	}
	sort.Slice(mains, func(i, j int) bool { return mains[i].count > mains[j].count })

	for _, m := range mains {
		fmt.Printf("\n  📁 %s (%d)\n", m.name, m.count)
		if subs, ok := subCount[m.name]; ok {
			subEntries := make([]entry, 0, len(subs))
			for k, v := range subs {
				subEntries = append(subEntries, entry{k, v})
			}
			sort.Slice(subEntries, func(i, j int) bool { return subEntries[i].count > subEntries[j].count })
			for _, s := range subEntries {
				fmt.Printf("     └─ %s: %d\n", s.name, s.count)
			}
		}
	}
}

func main() {
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("   Chrome 书签智能整理工具")
	fmt.Println(strings.Repeat("=", 60))

	loadEnv()

	profiles := findProfiles()
	if len(profiles) == 0 {
		fmt.Println("❌ 未找到 Chrome 配置文件")
		os.Exit(1)
	}

	profile := selectProfile(profiles)
	mode := selectMode()

	fmt.Printf("\n⚠️  请确认 Chrome 已关闭（避免写入冲突）\n")
	confirm := readLine("继续？[y/N]: ")
	if !strings.EqualFold(confirm, "y") {
		fmt.Println("已取消")
		return
	}

	// 读取
	fmt.Printf("\n📖 读取: %s\n", profile.Path)
	bf, err := ReadBookmarks(profile.Path)
	if err != nil {
		fmt.Printf("❌ 读取失败: %v\n", err)
		os.Exit(1)
	}

	// 展开 bookmark_bar（other/synced 保持不变）
	bookmarks := FlattenBookmarks(&bf.Roots.BookmarkBar)
	fmt.Printf("✅ 共 %d 个书签\n", len(bookmarks))

	// 去重
	unique, removed := Dedup(bookmarks)
	if len(removed) > 0 {
		fmt.Printf("   去重: 删除 %d 个重复，剩余 %d 个\n", len(removed), len(unique))
	}

	// 分类
	var classified map[CategoryKey][]Bookmark

	switch mode {
	case "ai":
		classified, err = ClassifyAI(unique)
		if err != nil {
			fmt.Printf("⚠️  AI 分类失败: %v\n   降级使用规则分类...\n", err)
			classified = ClassifyRules(unique)
		}
	default:
		fmt.Println("\n📏 规则分类中...")
		classified = ClassifyRules(unique)
	}

	printStats(classified)

	// 初始化 ID 计数器，避免 ID 冲突
	initIDCounter(bf)

	// 重建 bookmark_bar children
	fmt.Println("\n📂 重组书签结构...")
	now := chromeNow()
	bf.Roots.BookmarkBar.Children = BuildChildren(classified)
	bf.Roots.BookmarkBar.DateModified = now

	// 写回
	fmt.Printf("\n💾 写入书签文件...\n")
	if err := WriteBookmarks(profile.Path, bf); err != nil {
		fmt.Printf("❌ 写入失败: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("\n✅ 完成！重启 Chrome 即可查看整理后的书签。")
	fmt.Println(strings.Repeat("=", 60))
}
