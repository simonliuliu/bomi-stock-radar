# 中美太空股观察站 Pro

一个面向手机端的中美太空股/商业航天追踪网站。

## 功能
- 中美太空股样本看板
- 最新价、近1月、YTD、近1年表现
- 52周区间与历史位置
- 关注榜单与图表
- ACE 观点专区
- GitHub Actions 每日自动刷新数据并自动发布到 GitHub Pages

## 本地运行
```bash
cd /Users/simonsaiagent/.hermes/sites/space-stocks-pro
python3 scripts/update_data.py
python3 -m http.server 8766
```

## 自动部署
仓库推送到 GitHub 后，会通过 `.github/workflows/pages.yml`：
1. 每天自动运行数据刷新脚本
2. 发布静态站点到 GitHub Pages
