package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/openai/openai-go"
	"github.com/openai/openai-go/option"
)

const systemPrompt = `你是一个专业的书签分类助手。请根据书签的标题和URL，智能生成合适的分类。

核心规则：
1. 域名一致性：同一个域名的所有书签必须使用完全相同的分类
2. 分类粒度：主分类控制在8-15个，子分类仅在某类书签≥3个时创建
3. 禁止为1-2个书签创建独立主分类，应合并到相关大类
4. 主分类宽泛，子分类细化，避免语义重叠
5. 命名使用简洁中文，推荐主分类：技术开发、设计资源、工作相关、学习资料、AI、工具软件、金融投资、视频娱乐、新闻资讯、社交平台、云服务器
6. 必须为每个书签返回结果，不能遗漏

返回格式（sub 无子分类时填 null）：
{"results": [{"no": 0, "main": "技术开发", "sub": "代码仓库"}, {"no": 1, "main": "AI", "sub": null}]}`

// ---- AI 分类 ----

type aiResult struct {
	No   int    `json:"no"`
	Main string `json:"main"`
	Sub  string `json:"sub"`
}

type aiResponse struct {
	Results []aiResult `json:"results"`
}

func ClassifyAI(bookmarks []Bookmark) (map[CategoryKey][]Bookmark, error) {
	apiKey := os.Getenv("OPENROUTER_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("未设置 OPENROUTER_API_KEY")
	}
	model := os.Getenv("OPENROUTER_MODEL")
	if model == "" {
		model = "anthropic/claude-3.5-sonnet"
	}

	client := openai.NewClient(
		option.WithAPIKey(apiKey),
		option.WithBaseURL("https://openrouter.ai/api/v1"),
		option.WithHeader("HTTP-Referer", "https://github.com/zzfn/tabsort"),
		option.WithHeader("X-Title", "TabSort"),
		option.WithRequestTimeout(90*time.Second), // 单次请求（含重试）超时
	)

	result := make(map[CategoryKey][]Bookmark)
	total := len(bookmarks)
	batchSize := 1000

	fmt.Printf("🤖 AI 分类中...\n   模型: %s\n   总计: %d 个书签\n", model, total)

	for start := 0; start < total; start += batchSize {
		end := start + batchSize
		if end > total {
			end = total
		}
		batch := bookmarks[start:end]
		fmt.Printf("   处理 %d-%d/%d ...\n", start+1, end, total)

		type bmItem struct {
			No    int    `json:"no"`
			Title string `json:"title"`
			URL   string `json:"url"`
		}
		items := make([]bmItem, len(batch))
		for i, bm := range batch {
			items[i] = bmItem{No: start + i, Title: bm.Title, URL: bm.URL}
		}
		itemsJSON, _ := json.MarshalIndent(items, "", "  ")
		userMsg := fmt.Sprintf("请分类以下 %d 个书签，返回JSON格式：\n\n%s", len(batch), itemsJSON)

		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
		resp, err := client.Chat.Completions.New(ctx, openai.ChatCompletionNewParams{
			Model: openai.ChatModel(model),
			Messages: []openai.ChatCompletionMessageParamUnion{
				openai.SystemMessage(systemPrompt),
				openai.UserMessage(userMsg),
			},
			Temperature: openai.Float(0.3),
			ResponseFormat: openai.ChatCompletionNewParamsResponseFormatUnion{
				OfJSONObject: &openai.ResponseFormatJSONObjectParam{},
			},
		})
		cancel()
		if err != nil {
			var apierr *openai.Error
			if errors.As(err, &apierr) {
				return nil, fmt.Errorf("API 错误 %d: %s", apierr.StatusCode, apierr.Message)
			}
			return nil, fmt.Errorf("请求失败: %w", err)
		}

		var cr aiResponse
		if err := json.Unmarshal([]byte(resp.Choices[0].Message.Content), &cr); err != nil {
			return nil, fmt.Errorf("解析分类结果失败: %w", err)
		}

		processed := make(map[int]bool)
		for _, r := range cr.Results {
			batchIdx := r.No - start
			if batchIdx < 0 || batchIdx >= len(batch) {
				continue
			}
			key := CategoryKey{Main: r.Main, Sub: r.Sub}
			result[key] = append(result[key], batch[batchIdx])
			processed[batchIdx] = true
		}

		for i := range batch {
			if !processed[i] {
				key := CategoryKey{Main: "未分类"}
				result[key] = append(result[key], batch[i])
			}
		}
	}

	return result, nil
}

// ---- 规则分类 ----

type rule struct {
	domains  []string
	keywords []string
}

var rulesMap = map[string]rule{
	"AI": {
		domains:  []string{"openai.com", "anthropic.com", "perplexity.ai", "claude.ai", "chatgpt.com", "gemini.google.com"},
		keywords: []string{"chatgpt", "claude", "openai", "anthropic", "gpt", "llm", "gemini", "copilot"},
	},
	"技术开发": {
		domains:  []string{"github.com", "stackoverflow.com", "juejin.cn", "v2ex.com", "zhihu.com", "segmentfault.com", "gitee.com", "gitlab.com"},
		keywords: []string{"github", "stackoverflow", "juejin", "v2ex", "segmentfault"},
	},
	"云服务器": {
		domains:  []string{"aliyun.com", "aws.amazon.com", "cloudflare.com", "vercel.com", "netlify.com", "cloud.tencent.com", "digitalocean.com"},
		keywords: []string{"aliyun", "cloudflare", "vercel", "netlify", "heroku", "aws"},
	},
	"设计资源": {
		domains:  []string{"figma.com", "dribbble.com", "behance.net", "framer.com"},
		keywords: []string{"figma", "dribbble", "design", "ui kit"},
	},
	"工具软件": {
		domains:  []string{"excalidraw.com", "tinypng.com", "notion.so", "feishu.cn"},
		keywords: []string{"excalidraw", "tinypng", "notion", "feishu"},
	},
	"金融投资": {
		domains:  []string{"tradingview.com", "binance.com", "coinbase.com", "xueqiu.com", "eastmoney.com"},
		keywords: []string{"trading", "stock", "finance", "invest", "etf", "option", "crypto"},
	},
	"视频娱乐": {
		domains:  []string{"youtube.com", "netflix.com", "bilibili.com", "twitch.tv"},
		keywords: []string{"youtube", "netflix", "bilibili", "movie", "anime"},
	},
	"工作相关": {
		domains:  []string{"nioint.com", "nevint.com"},
		keywords: []string{"confluence", "jira"},
	},
}

func ClassifyRules(bookmarks []Bookmark) map[CategoryKey][]Bookmark {
	result := make(map[CategoryKey][]Bookmark)
	for _, bm := range bookmarks {
		domain := bm.Domain()
		combined := strings.ToLower(bm.Title + " " + bm.URL)
		key := CategoryKey{Main: matchRule(domain, combined)}
		result[key] = append(result[key], bm)
	}
	return result
}

func matchRule(domain, combined string) string {
	for cat, r := range rulesMap {
		for _, d := range r.domains {
			if domain == d || strings.HasSuffix(domain, "."+d) {
				return cat
			}
		}
	}
	for cat, r := range rulesMap {
		for _, kw := range r.keywords {
			if strings.Contains(combined, kw) {
				return cat
			}
		}
	}
	return "其他"
}
