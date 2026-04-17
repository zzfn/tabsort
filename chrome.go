package main

import (
	"crypto/rand"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"
)

// Chrome Bookmarks JSON 结构
type BookmarksFile struct {
	Checksum     string         `json:"checksum"`
	Roots        BookmarksRoots `json:"roots"`
	SyncMetadata string         `json:"sync_metadata,omitempty"`
	Version      int            `json:"version"`
}

type BookmarksRoots struct {
	BookmarkBar BookmarkNode `json:"bookmark_bar"`
	Other       BookmarkNode `json:"other"`
	Synced      BookmarkNode `json:"synced"`
}

type BookmarkNode struct {
	Children     []BookmarkNode  `json:"children,omitempty"`
	DateAdded    string          `json:"date_added,omitempty"`
	DateLastUsed string          `json:"date_last_used,omitempty"`
	DateModified string          `json:"date_modified,omitempty"`
	GUID         string          `json:"guid,omitempty"`
	ID           string          `json:"id"`
	MetaInfo     json.RawMessage `json:"meta_info,omitempty"`
	Name         string          `json:"name"`
	Type         string          `json:"type"`
	URL          string          `json:"url,omitempty"`
}

// 扁平书签
type Bookmark struct {
	Title        string
	URL          string
	DateAdded    string
	DateLastUsed string
	GUID         string
	ID           string
}

func (b *Bookmark) Domain() string {
	u, err := url.Parse(b.URL)
	if err != nil {
		return ""
	}
	return strings.TrimPrefix(u.Hostname(), "www.")
}

// URL 去除 fragment 后的 key
func urlKey(rawURL string) string {
	u, err := url.Parse(rawURL)
	if err != nil {
		return rawURL
	}
	u.Fragment = ""
	return u.String()
}

func ReadBookmarks(path string) (*BookmarksFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var bf BookmarksFile
	if err := json.Unmarshal(data, &bf); err != nil {
		return nil, err
	}
	return &bf, nil
}

func WriteBookmarks(path string, bf *BookmarksFile) error {
	// 备份原文件
	backupPath := path + ".bak." + time.Now().Format("20060102_150405")
	if orig, err := os.ReadFile(path); err == nil {
		if err := os.WriteFile(backupPath, orig, 0600); err != nil {
			return fmt.Errorf("备份失败: %w", err)
		}
		fmt.Printf("✅ 已备份到: %s\n", backupPath)
	}

	// 清空 checksum，Chrome 重启时会自动重新计算
	bf.Checksum = ""

	data, err := json.MarshalIndent(bf, "", "   ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0600)
}

// 递归展开书签栏中所有 url 节点
func FlattenBookmarks(node *BookmarkNode) []Bookmark {
	var result []Bookmark
	for i := range node.Children {
		child := &node.Children[i]
		switch child.Type {
		case "url":
			result = append(result, Bookmark{
				Title:        child.Name,
				URL:          child.URL,
				DateAdded:    child.DateAdded,
				DateLastUsed: child.DateLastUsed,
				GUID:         child.GUID,
				ID:           child.ID,
			})
		case "folder":
			result = append(result, FlattenBookmarks(child)...)
		}
	}
	return result
}

// 按 URL 去重（完全相同的 URL）
func Dedup(bookmarks []Bookmark) (unique []Bookmark, removed []Bookmark) {
	seen := make(map[string]bool)
	for _, bm := range bookmarks {
		key := bm.URL
		if seen[key] {
			removed = append(removed, bm)
			continue
		}
		seen[key] = true
		unique = append(unique, bm)
	}
	return
}

// ---- ID / GUID 工具 ----

var nextID int

func initIDCounter(bf *BookmarksFile) {
	m := scanMaxID(&bf.Roots.BookmarkBar)
	if m2 := scanMaxID(&bf.Roots.Other); m2 > m {
		m = m2
	}
	if m3 := scanMaxID(&bf.Roots.Synced); m3 > m {
		m = m3
	}
	nextID = m + 1
}

func scanMaxID(node *BookmarkNode) int {
	id, _ := strconv.Atoi(node.ID)
	max := id
	for i := range node.Children {
		if m := scanMaxID(&node.Children[i]); m > max {
			max = m
		}
	}
	return max
}

func newID() string {
	id := nextID
	nextID++
	return strconv.Itoa(id)
}

func newGUID() string {
	b := make([]byte, 16)
	rand.Read(b)
	b[6] = (b[6] & 0x0f) | 0x40 // version 4
	b[8] = (b[8] & 0x3f) | 0x80 // variant bits
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x",
		b[0:4], b[4:6], b[6:8], b[8:10], b[10:16])
}

// Chrome 时间戳：自 1601-01-01 起的微秒数
func chromeNow() string {
	const delta = int64(11644473600 * 1_000_000)
	micros := time.Now().UnixMicro() + delta
	return strconv.FormatInt(micros, 10)
}

// ---- 构建新的书签树 ----

type CategoryKey struct {
	Main string
	Sub  string
}

// BuildChildren 将分类结果转换为 []BookmarkNode
func BuildChildren(classified map[CategoryKey][]Bookmark) []BookmarkNode {
	now := chromeNow()

	// 按主分类聚合
	type subGroup struct {
		sub  string
		bms  []Bookmark
	}
	mainMap := make(map[string][]subGroup)
	var mainOrder []string

	for key, bms := range classified {
		if _, exists := mainMap[key.Main]; !exists {
			mainOrder = append(mainOrder, key.Main)
		}
		mainMap[key.Main] = append(mainMap[key.Main], subGroup{sub: key.Sub, bms: bms})
	}
	sort.Strings(mainOrder)

	var children []BookmarkNode

	for _, main := range mainOrder {
		groups := mainMap[main]

		// 整理子分类
		sort.Slice(groups, func(i, j int) bool { return groups[i].sub < groups[j].sub })

		mainFolder := BookmarkNode{
			DateAdded:    now,
			DateModified: now,
			GUID:         newGUID(),
			ID:           newID(),
			Name:         main,
			Type:         "folder",
		}

		var mainChildren []BookmarkNode

		for _, g := range groups {
			if g.sub == "" {
				// 直接挂在主分类下
				for _, bm := range g.bms {
					mainChildren = append(mainChildren, bmToNode(bm, now))
				}
			} else {
				subFolder := BookmarkNode{
					DateAdded:    now,
					DateModified: now,
					GUID:         newGUID(),
					ID:           newID(),
					Name:         g.sub,
					Type:         "folder",
				}
				var subChildren []BookmarkNode
				for _, bm := range g.bms {
					subChildren = append(subChildren, bmToNode(bm, now))
				}
				subFolder.Children = subChildren
				mainChildren = append(mainChildren, subFolder)
			}
		}

		mainFolder.Children = mainChildren
		children = append(children, mainFolder)
	}

	return children
}

func bmToNode(bm Bookmark, now string) BookmarkNode {
	guid := bm.GUID
	if guid == "" {
		guid = newGUID()
	}
	id := bm.ID
	if id == "" {
		id = newID()
	}
	dateAdded := bm.DateAdded
	if dateAdded == "" {
		dateAdded = now
	}
	return BookmarkNode{
		DateAdded:    dateAdded,
		DateLastUsed: bm.DateLastUsed,
		GUID:         guid,
		ID:           id,
		Name:         bm.Title,
		Type:         "url",
		URL:          bm.URL,
	}
}
