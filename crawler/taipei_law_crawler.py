"""
台北市法規爬蟲模塊
爬取台北市法規資料庫的法規內容
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.parse import urljoin

from config import TAIPEI_LAW_CONFIG
from crawler.base_crawler import BaseLawCrawler


class TaipeiLawCrawler(BaseLawCrawler):
    """
    台北市法規資料庫爬蟲
    """
    
    def __init__(self):
        """
        初始化台北市法規爬蟲
        """
        super().__init__(TAIPEI_LAW_CONFIG)
        self.base_url = TAIPEI_LAW_CONFIG['base_url']
    
    def get_total_pages(self) -> int:
        """
        獲取法規列表的總頁數
        
        Returns:
            總頁數
        """
        try:
            url = f"{self.base_url}/{TAIPEI_LAW_CONFIG['category_url'].format(1)}"
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            total_pages = int(soup.select_one("div.paging-counts em:nth-of-type(2)").text)
            logging.info(f"總頁數: {total_pages}")
            return total_pages
        except Exception as e:
            logging.error(f"獲取總頁數時出錯: {e}")
            return 0
    
    def get_law_urls(self) -> List[str]:
        """
        獲取所有法規頁面的鏈接
        
        Returns:
            法規頁面鏈接列表
        """
        urls = []
        total_pages = self.get_total_pages()
        
        if total_pages == 0:
            return urls
        
        for page in range(1, total_pages + 1):
            try:
                self.random_delay()
                page_url = f"{self.base_url}/{TAIPEI_LAW_CONFIG['category_url'].format(page)}"
                response = self.session.get(page_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.select("table.table-tab td a"):
                    if 'href' in link.attrs:
                        law_url = urljoin(self.base_url, link['href'])
                        urls.append(law_url)
                logging.info(f"已處理第 {page}/{total_pages} 頁")
            except Exception as e:
                logging.error(f"處理第 {page} 頁時出錯: {e}")
        
        logging.info(f"找到 {len(urls)} 個法規鏈接")
        return urls
    
    def get_law_json(self, url: str) -> Optional[Dict[str, Any]]:
        """
        獲取單個法規的 JSON 數據
        
        Args:
            url: 法規頁面 URL
            
        Returns:
            包含法規信息的字典，或在失敗時返回 None
        """
        try:
            fl_code = url.split('/FL')[1].split('?')[0]
            info_url = f"{self.base_url}/Law/LawSearch/LawInformation/FL{fl_code}"
            content_url = f"{self.base_url}/Law/LawSearch/LawArticleContent/FL{fl_code}"
            
            # 獲取法規基本信息
            response = self.session.get(info_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            law_name_elem = soup.select_one("div.col-input a.law-link")
            modified_date_elem = soup.select_one("div.col-label:contains('修正日期') + div.col-input dfn")
            
            law_data = {
                "LawName": self._get_text(law_name_elem),
                "LawModifiedDate": self._get_text(modified_date_elem),
                "LawArticles": [],
                "LawURL": content_url
            }
            
            # 獲取法規條文內容
            self.random_delay()
            response = self.session.get(content_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.select("ul.law.law-content li")
            chapter = ""
            
            for article in articles:
                self._process_article(article, chapter, law_data)
            
            if not law_data["LawName"]:
                logging.error(f"未找到法規名稱: {content_url}")
                return None
                
            return law_data
        except Exception as e:
            logging.error(f"處理 URL 失敗: {url}")
            logging.error(f"錯誤: {str(e)}")
            return None
    
    def _process_article(self, article: Tag, chapter: str, law_data: Dict[str, Any]) -> None:
        """
        處理單個法規條文
        
        Args:
            article: 條文 HTML 元素
            chapter: 當前章節
            law_data: 法規數據字典
        """
        # 處理章節標題
        if article.select_one("div.law-articlepre") is None and article.text.strip():
            chapter = article.text.strip()
            return
            
        content_div = article.select_one("div.law-articlepre")
        if content_div:
            content = content_div.text.strip()
            
            # 檢查是否為點號形式(如 "一、") 或條號形式(如 "第1條")
            if re.match(r'^[一二三四五六七八九十]+、', content):
                number = content.split('、')[0] + '、'
                content = content[len(number):].strip()
            else:
                number_div = article.select_one("div.col-no")
                number = self._get_text(number_div)
            
            if content:
                law_data["LawArticles"].append({
                    "Chapter": chapter,
                    "ArticleNo": number,
                    "ArticleContent": content
                })
    
    def _get_text(self, element: Optional[Tag]) -> str:
        """
        安全地獲取元素的文本
        
        Args:
            element: HTML 元素
            
        Returns:
            元素的文本，如果元素不存在則返回空字符串
        """
        return element.text.strip() if element else ""
    
    def process_law(self, url: str) -> bool:
        """
        處理單個法規鏈接
        
        Args:
            url: 法規頁面 URL
            
        Returns:
            處理是否成功
        """
        law_data = self.get_law_json(url)
        if law_data and law_data["LawName"]:
            filename = f"{law_data['LawName']}.json"
            self.save_json(law_data, filename)
            return True
        return False
    
    def run(self) -> None:
        """
        運行台北市法規爬蟲
        """
        law_urls = self.get_law_urls()
        
        if not law_urls:
            logging.error("未找到法規鏈接")
            return
            
        processed_count = self.process_batch(law_urls, self.process_law, "處理法規中")
        
        logging.info(f"完成！成功處理了 {processed_count} / {len(law_urls)} 個法規")


if __name__ == "__main__":
    crawler = TaipeiLawCrawler()
    crawler.run()
