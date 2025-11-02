# 分类配置
CATEGORIES = {
    "技术学习": {
        "keywords": ["github", "stackoverflow", "csdn", "juejin", "segmentfault", "v2ex", "cnblogs", "zhihu"],
        "domains": ["github.com", "stackoverflow.com", "juejin.cn", "segmentfault.com", "v2ex.com", "cnblogs.com", "zhihu.com", "zhuanlan.zhihu.com"],
        "url_patterns": ["blog", "tutorial", "doc", "api", "guide"],
        "subcategories": {
            "掘金": {
                "keywords": ["juejin"],
                "domains": ["juejin.cn"]
            },
            "V2EX": {
                "keywords": ["v2ex"],
                "domains": ["v2ex.com"]
            },
            "知乎": {
                "keywords": ["zhihu"],
                "domains": ["zhihu.com", "zhuanlan.zhihu.com"]
            },
            "前端开发": {
                "keywords": ["react", "vue", "javascript", "js", "css", "html", "webpack", "vite", "npm", "typescript", "ts", "tailwind", "next", "nuxt"],
                "domains": ["react.dev", "vuejs.org", "developer.mozilla.org", "css-tricks.com", "tailwindcss.com"]
            },
            "后端开发": {
                "keywords": ["java", "python", "go", "golang", "spring", "django", "flask", "node", "express", "nest"],
                "domains": ["spring.io", "django", "golang.org", "nodejs.org"]
            },
            "数据库": {
                "keywords": ["mysql", "mongodb", "redis", "postgresql", "sql", "database"],
                "domains": ["mongodb.com", "redis.io", "postgresql.org"]
            },
            "运维/DevOps": {
                "keywords": ["docker", "kubernetes", "k8s", "nginx", "jenkins", "gitlab", "ci/cd", "devops"],
                "domains": ["kubernetes.io", "docker.com", "nginx.com"]
            },
            "代码仓库": {
                "keywords": ["github", "gitlab", "gitee", "repository"],
                "domains": ["github.com", "gitlab.com", "gitee.com"]
            }
        }
    },
    "工作相关": {
        "keywords": ["feishu", "nio", "confluence", "jira", "wiki"],
        "domains": ["feishu.cn", "nioint.com", "nevint.com"],
        "subcategories": {
            "飞书文档": {
                "domains": ["feishu.cn"]
            },
            "内部系统": {
                "domains": ["nioint.com", "nevint.com"]
            }
        }
    },
    "设计资源": {
        "keywords": ["design", "ui", "ux", "figma", "color", "icon", "font", "dribbble", "behance"],
        "domains": ["dribbble.com", "behance.net", "figma.com", "framer.com", "pinterest.com"],
        "subcategories": {
            "UI组件库": {
                "keywords": ["component", "ui", "antd", "element", "material", "chakra", "radix", "shadcn"],
                "domains": ["mui.com", "ant.design", "chakra-ui.com", "radix-ui.com"]
            },
            "图标字体": {
                "keywords": ["icon", "font", "iconfont"],
                "domains": ["iconfont.cn", "fontawesome.com", "iconpark.oceanengine.com"]
            },
            "配色工具": {
                "keywords": ["color", "palette"],
                "domains": ["nipponcolors.com", "zhongguose.com", "colordesigner.io"]
            }
        }
    },
    "工具软件": {
        "keywords": ["tool", "converter", "editor", "generator", "online"],
        "domains": ["stackoverflow.com"],
        "subcategories": {
            "在线工具": {
                "keywords": ["online", "convert", "editor", "generator"],
                "domains": ["carbon.now.sh", "excalidraw.com", "processon.com", "tinypng.com"]
            },
            "开发工具": {
                "keywords": ["stackblitz", "codesandbox", "playground", "repl"],
                "domains": ["stackblitz.com", "codesandbox.io", "replit.com"]
            },
            "下载工具": {
                "keywords": ["download", "torrent", "下载", "motrix"],
                "domains": ["motrix.app", "thepiratebay.org"]
            },
            "图片处理": {
                "keywords": ["image", "photo", "picture", "图片", "截图"],
                "domains": []
            }
        }
    },
    "资讯媒体": {
        "keywords": ["news", "medium", "blog"],
        "domains": ["medium.com", "mp.weixin.qq.com", "sspai.com", "tophub.today"],
        "subcategories": {
            "技术博客": {
                "keywords": ["blog", "tech"],
                "domains": ["overreacted.io", "kentcdodds.com", "joshwcomeau.com"]
            },
            "微信公众号": {
                "domains": ["mp.weixin.qq.com"]
            }
        }
    },
    "投资理财": {
        "keywords": ["stock", "trading", "finance", "invest", "etf", "option"],
        "domains": ["tradingview.com", "barchart.com", "yahoo.com", "finviz.com", "alpaca.markets", "etf.com"],
        "subcategories": {
            "行情分析": {
                "keywords": ["chart", "analysis", "tradingview"],
                "domains": ["tradingview.com", "barchart.com", "finviz.com"]
            },
            "期权工具": {
                "keywords": ["option", "optionstrat"],
                "domains": ["optionstrat.com", "optioncharts.io"]
            }
        }
    },
    "学习资源": {
        "keywords": ["tutorial", "course", "learn", "doc", "documentation", "leetcode"],
        "domains": ["leetcode.cn", "nowcoder.com", "luogu.com.cn"],
        "subcategories": {
            "算法刷题": {
                "keywords": ["leetcode", "algorithm", "牛客"],
                "domains": ["leetcode.cn", "nowcoder.com", "luogu.com.cn", "codetop.cc"]
            },
            "技术文档": {
                "keywords": ["doc", "documentation", "api", "reference"],
                "domains": ["developer.mozilla.org", "docs.microsoft.com"]
            }
        }
    },
    "娱乐生活": {
        "keywords": ["music", "video", "movie", "game", "netflix", "youtube", "steam"],
        "domains": ["youtube.com", "netflix.com", "steam", "pixiv.net"],
        "subcategories": {
            "影视": {
                "keywords": ["movie", "tv", "netflix", "disney"],
                "domains": ["netflix.com", "disneyplus.com", "themoviedb.org", "justwatch.com"]
            },
            "音乐": {
                "keywords": ["music"],
                "domains": ["musicforprogramming.net"]
            }
        }
    },
    "AI": {
        "keywords": ["ai", "gpt", "claude", "chatgpt", "openai", "anthropic", "perplexity", "llm", "人工智能", "机器学习", "gemini"],
        "domains": ["anthropic.com", "openai.com", "perplexity.ai", "siliconflow.cn", "aiagenttoolkit.xyz", "ctok.ai", "vercel.ai", "langfuse.com"],
        "subcategories": {
            "AI对话": {
                "keywords": ["chat", "gpt", "claude", "chatgpt"],
                "domains": ["anthropic.com", "openai.com", "perplexity.ai", "nio.feishu.cn"]
            },
            "AI绘图": {
                "keywords": ["image", "draw", "midjourney", "stable", "ideogram", "dalle"],
                "domains": ["ideogram.ai", "craiyon.com", "designer.microsoft.com"]
            },
            "AI开发": {
                "keywords": ["code", "编程", "开发", "claude code", "api", "ai tool", "ai playground"],
                "domains": ["play.vercel.ai", "langfuse.com", "ctok.ai"]
            }
        }
    }
}

# 默认分类（无法匹配时）
DEFAULT_CATEGORY = "其他"

# 最小分类阈值（书签数量少于此值的子分类会被合并到父分类）
MIN_CATEGORY_SIZE = 3
