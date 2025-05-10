# LawCrawler 台灣法律條文爬蟲工具 (重構版)

一個用於爬取台灣法律法規的專業工具，支援中央法規及地方法規（台北市、新北市、桃園市、台中市、高雄市）。此版本為重構版，優化了代碼結構和風格。

## 重構特點

- **模組化設計**：採用基於類的繼承結構，實現代碼重用
- **配置集中管理**：所有配置參數統一在 `config.py` 中管理
- **類型註解**：使用 Python 類型提示增強代碼可讀性
- **一致的代碼風格**：遵循 PEP 8 標準和 Clean Code 原則
- **完善的文檔**：每個模組、類、方法都有詳細的文檔字符串

## 功能特色

- 多源爬取：支援中央法規、台北市法規及其他地方法規
- 高效並行：使用 ThreadPoolExecutor 實現多線程爬取
- 異常處理：完善的重試機制和日誌記錄
- 結構化存儲：以 JSON 格式保存所有法規數據
- 用戶友好：帶有進度條顯示，清晰展示爬取進度

## 支援來源

| 來源 | 網址 | 狀態 |
|------|------|------|
| 中央法規 | https://law.moj.gov.tw/ | ✅ 支援 |
| 台北市法規 | https://www.laws.taipei.gov.tw/Law | ✅ 支援 |
| 新北市法規 | https://web.law.ntpc.gov.tw/ | ✅ 支援 |
| 桃園市法規 | https://law.tycg.gov.tw/ | ✅ 支援 |
| 台中市法規 | https://law.taichung.gov.tw/ | ✅ 支援 |
| 高雄市法規 | https://outlaw.kcg.gov.tw/LawQuery.aspx | ✅ 支援 |
| 台南市法規 | https://law01.tainan.gov.tw/glrsnewsout/ | ❌ 不支援 |
| 其他縣市法規 | | ❌ 不支援 |

## 代碼結構

```
LawCrawler-Refactored/
├── config.py              # 配置文件
├── main.py                # 主入口腳本
├── requirements.txt       # 依賴項
├── crawler/               # 爬蟲包
│   ├── __init__.py        # 包初始化
│   ├── base_crawler.py    # 基礎爬蟲類
│   ├── central_law_crawler.py  # 中央法規爬蟲
│   └── taipei_law_crawler.py   # 台北市法規爬蟲
```

## 安裝

### 前置需求

- Python 3.8+
- pip 套件管理工具

### 步驟

1. 克隆儲存庫

```bash
git clone https://github.com/audi0417/LawCrawler-Refactored.git
cd LawCrawler-Refactored
```

2. 安裝依賴套件

```bash
pip install -r requirements.txt
```

## 使用方法

### 爬取所有來源的法規

```bash
python main.py
```

### 爬取特定來源的法規

```bash
python main.py --source central  # 爬取中央法規
python main.py --source taipei   # 爬取台北市法規
```

### 直接運行特定爬蟲模塊

```bash
python -m crawler.central_law_crawler  # 爬取中央法規
python -m crawler.taipei_law_crawler   # 爬取台北市法規
```

## 輸出格式

所有爬取的法規都會以 JSON 格式保存，基本結構如下：

```json
{
  "LawName": "法規名稱",
  "LawCategory": "法規分類",
  "LawModifiedDate": "最後修改日期",
  "LawArticles": [
    {
      "ArticleNo": "條號",
      "ArticleContent": "條文內容"
    }
  ],
  "LawURL": "原始網址"
}
```

## 擴展指南

要添加對新的法規來源的支持，請按以下步驟操作：

1. 在 `config.py` 中添加新來源的配置
2. 創建一個繼承自 `BaseLawCrawler` 的新爬蟲類
3. 實現必要的方法：`get_law_urls()`, `get_law_json()`, `run()`
4. 在 `main.py` 中添加對新爬蟲的調用

例如，添加對新的縣市法規的支持：

```python
class NewCityLawCrawler(BaseLawCrawler):
    def __init__(self):
        super().__init__(NEW_CITY_LAW_CONFIG)
        
    def get_law_urls(self):
        # 實現獲取法規鏈接的邏輯
        
    def get_law_json(self, url):
        # 實現獲取和解析法規內容的邏輯
        
    def run(self):
        # 實現爬蟲運行流程
```

## 效能調優

已內置的效能優化：

- 使用連接池重用 HTTP 連接
- 批量處理 URL，減少記憶體佔用
- 進度條顯示，實時監控爬取進度
- 指數退避重試機制，處理網路不穩定情況

## 常見問題

**Q: 爬取過程中遇到 HTTP 錯誤怎麼辦？**  
A: 程式已內建重試機制，會自動重試失敗的請求。如果問題持續存在，請檢查日誌文件了解詳情。

**Q: 如何調整爬取速度？**  
A: 您可以在 `config.py` 中調整 `delay_min`, `delay_max` 和 `max_workers` 參數來控制爬取速度。

**Q: 如何添加對新的法規來源的支持？**  
A: 請參考「擴展指南」章節。

## 貢獻指南

歡迎提交 Pull Request 或建立 Issue！

1. Fork 此倉庫
2. 創建您的功能分支：`git checkout -b feature/amazing-feature`
3. 提交您的更改：`git commit -m 'Add some amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

## 免責聲明

本工具僅供研究和學習使用。請尊重各法規網站的使用條款，不要過度頻繁地訪問這些網站。用戶須自行承擔使用本工具的法律責任。

## 授權

本專案採用 MIT 授權 - 詳情請參閱 [LICENSE](LICENSE) 文件

## 作者

**陳楷融** - [GitHub Profile](https://github.com/audi0417)

如果您覺得這個專案有幫助，請給它一個 ⭐️！

## 更新日誌

- **v2.0.0** (2025-05-10)
  - 完全重構代碼架構
  - 實現基於類的繼承設計
  - 統一代碼風格和命名約定
  - 添加完整的類型註解和文檔

---

Made with ❤️ in Taiwan
