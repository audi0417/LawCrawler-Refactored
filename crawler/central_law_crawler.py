"""
中央法規爬蟲模塊
爬取中央法規資料庫的法規內容
"""

import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.parse import urljoin

from config import CENTRAL_LAW_CONFIG
from crawler.base_crawler import BaseLawCrawler


class CentralLawCrawler(BaseLawCrawler):
    """
    中央法規資料庫爬蟲
    """
    
    def __init__(self):
        """
        初始化中央法規爬蟲
        """
        super().__init__(CENTRAL_LAW_CONFIG)
        self.base_url = CENTRAL_LAW_CONFIG['base_url']
    
    def get_category_links(self) -> Tuple[List[str], int]:
        """
        獲取所有法規分類頁面的鏈接
        
        Returns:
            包含分類鏈接列表和估計法規總數的元組
        """
        try:
            response = self.session.get(self.base_url + CENTRAL_LAW_CONFIG['search_url'])
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            self._parse_category_tree(soup.find('ul', id='tree'), links)
            
            total_laws = sum(int(span.text) for span in soup.select('span.badge') 
                           if span.text.isdigit())
            
            logging.info(f"找到 {len(links)} 個分類連結，估計有 {total_laws} 條法規")
            
            return links, total_laws
        except Exception as e:
            logging.error(f"獲取分類連結時出錯: {e}")
            return [], 0
    
    def _parse_category_tree(self, element: Optional[Tag], links: List[str]) -> None:
        """
        遞歸解析法規分類樹
        
        Args:
            element: 要解析的 HTML 元素
            links: 存儲發現的鏈接的列表
        """
        if not element:
            return
            
        if element.name == 'a':
            if 'LawSearchLaw.aspx?TY=' in element.get('href', ''): 
                href = urljoin(self.base_url, element['href'])
                if 'fei=1' not in href:  # 排除廢止的法規
                    links.append(href)
            elif 'javascript:void(0)' in element.get('href', ''):
                next_ul = element.find_next('ul')
                if next_ul:
                    self._parse_category_tree(next_ul, links)
                    
        for child in element.children:
            if isinstance(child, Tag):
                self._parse_category_tree(child, links)
    
    def get_law_links(self, category_url: str) -> List[str]:
        """
        從分類頁面獲取法規鏈接
        
        Args:
            category_url: 分類頁面 URL
            
        Returns:
            法規頁面鏈接列表
        """
        try:
            self.random_delay()
            response = self.session.get(category_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            table = soup.find('table', {'class': 'table table-hover tab-list tab-central'})
            if table:
                for a in table.find_all('a', href=re.compile(r'LawAll\\.aspx\\?PCODE=')):
                    href = urljoin("https://law.moj.gov.tw", a['href'])
                    links.append(href)
            return links
        except Exception as e:
            logging.error(f"獲取 {category_url} 的法規鏈接時出錯: {e}")
            return []
    
    def get_law_json(self, url: str) -> Optional[Dict[str, Any]]:
        """
        獲取單個法規的 JSON 數據
        
        Args:
            url: 法規頁面 URL
            
        Returns:
            包含法規信息的字典，或在失敗時返回 None
        """
        try:
            self.random_delay()
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            modified_date_elem = (
                soup.select_one("#trLNNDate td") or 
                soup.select_one("#trLNODate td") or
                soup.select_one(".table-title tr:contains('修正日期') td")
            )
            
            law_data = {
                "LawName": self._get_text(soup.select_one("#hlLawName")),
                "LawCategory": self._get_text(soup.select_one(".table tr:nth-child(3) td")),
                "LawModifiedDate": ''.join(filter(str.isdigit, self._get_text(modified_date_elem))),
                "LawHistories": "",
                "LawArticles": [],
                "LawURL": url
            }
            
            rows = soup.select('.row')
            for row in rows:
                article_no = row.select_one('.col-no a')
                article = row.select_one('.law-article')
                if article_no and article:
                    law_data["LawArticles"].append({
                        "ArticleNo": f"{law_data['LawName']}, {self._get_text(article_no)}",
                        "ArticleContent": self._get_text(article)
                    })
            
            return law_data
            
        except Exception as e:
            logging.error(f"處理 URL 失敗: {url}")
            logging.error(f"錯誤: {str(e)}")
            return None
    
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
        運行中央法規爬蟲
        """
        category_links, total_laws = self.get_category_links()
        
        if not category_links:
            logging.error("未找到分類連結")
            return
            
        all_law_urls = []
        for category_url in category_links:
            urls = self.get_law_links(category_url)
            all_law_urls.extend(urls)
        
        logging.info(f"找到 {len(all_law_urls)} 個法規 URL")
        
        processed_count = self.process_batch(all_law_urls, self.process_law, "處理法規中")
        
        logging.info(f"完成！成功處理了 {processed_count} 個法規")


if __name__ == "__main__":
    crawler = CentralLawCrawler()
    crawler.run()
