"""
中央法規爬蟲模塊
爬取中央法規資料庫的法規內容
"""

import logging
import re
import time
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
            
            # 調整：如果找不到樹形結構，嘗試直接獲取分類鏈接
            if not links and soup.select('a[href*="LawSearchLaw.aspx?TY="]'):
                for a in soup.select('a[href*="LawSearchLaw.aspx?TY="]'):
                    href = urljoin(self.base_url, a['href'])
                    if 'fei=1' not in href:  # 排除廢止的法規
                        links.append(href)
            
            # 獲取法規總數，如果找不到則使用估計值
            total_laws = 0
            try:
                badge_spans = soup.select('span.badge')
                total_laws = sum(int(span.text) for span in badge_spans if span.text.isdigit())
            except:
                total_laws = len(links) * 10  # 估計值
            
            logging.info(f"找到 {len(links)} 個分類連結，估計有 {total_laws} 條法規")
            
            # 如果仍然找不到分類鏈接，使用緊急方案
            if not links:
                logging.warning("找不到分類連結，使用緊急方案直接訪問特定法規分類")
                # 添加一些已知的重要法規分類
                emergency_links = [
                    "https://law.moj.gov.tw/LawSearchLaw.aspx?TY=01000",  # 憲法
                    "https://law.moj.gov.tw/LawSearchLaw.aspx?TY=02000",  # 民法
                    "https://law.moj.gov.tw/LawSearchLaw.aspx?TY=03000",  # 刑法
                    "https://law.moj.gov.tw/LawSearchLaw.aspx?TY=04000"   # 行政法
                ]
                links.extend(emergency_links)
                logging.info(f"緊急方案添加了 {len(emergency_links)} 個分類連結")
            
            return links, total_laws
        except Exception as e:
            logging.error(f"獲取分類連結時出錯: {e}")
            # 緊急方案，提供一些基本分類鏈接
            emergency_links = [
                "https://law.moj.gov.tw/LawSearchLaw.aspx?TY=01000",  # 憲法
                "https://law.moj.gov.tw/LawSearchLaw.aspx?TY=02000",  # 民法
                "https://law.moj.gov.tw/LawSearchLaw.aspx?TY=03000",  # 刑法
                "https://law.moj.gov.tw/LawSearchLaw.aspx?TY=04000"   # 行政法
            ]
            return emergency_links, len(emergency_links) * 10
    
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
            
            # 嘗試使用多種選擇器來查找法規連結
            selectors = [
                'table.table.table-hover.tab-list.tab-central a[href*="LawAll.aspx?PCODE="]',
                'table a[href*="LawAll.aspx?PCODE="]',
                'a[href*="LawAll.aspx?PCODE="]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for a in elements:
                        href = urljoin("https://law.moj.gov.tw", a['href'])
                        links.append(href)
                    break  # 如果找到了鏈接，就跳出循環
            
            # 如果仍然找不到，嘗試使用正則表達式
            if not links:
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    if re.search(r'LawAll\.aspx\?PCODE=', href):
                        full_href = urljoin("https://law.moj.gov.tw", href)
                        links.append(full_href)
            
            # 如果仍然找不到，嘗試獲取頁面上的任何鏈接，以便調試
            if not links:
                debug_links = []
                for a in soup.find_all('a', href=True):
                    debug_links.append(a['href'])
                
                logging.warning(f"在 {category_url} 找不到法規鏈接")
                logging.warning(f"頁面上的所有鏈接: {debug_links[:10]} ... (總計 {len(debug_links)} 個)")
                
                # 儲存頁面 HTML 用於調試
                logging.debug(f"頁面內容: {response.text[:1000]} ... (省略)")
            
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
            
            # 嘗試多種方式獲取修改日期
            modified_date_elem = None
            date_selectors = [
                "#trLNNDate td", 
                "#trLNODate td",
                ".table-title tr:contains('修正日期') td",
                "tr:contains('修正日期') td",
                "tr:contains('公布日期') td"
            ]
            
            for selector in date_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        modified_date_elem = elem
                        break
                except:
                    continue
            
            # 獲取法規名稱
            law_name = ""
            name_selectors = ["#hlLawName", ".law-title", "h2", "h1", "title"]
            for selector in name_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem and elem.text.strip():
                        law_name = elem.text.strip()
                        break
                except:
                    continue
            
            # 獲取法規分類
            law_category = ""
            category_selectors = [
                ".table tr:nth-child(3) td",
                "tr:contains('法規類別') td"
            ]
            for selector in category_selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem and elem.text.strip():
                        law_category = elem.text.strip()
                        break
                except:
                    continue
            
            # 如果找不到法規名稱，記錄錯誤並返回 None
            if not law_name:
                logging.error(f"找不到法規名稱: {url}")
                # 保存頁面內容用於調試
                logging.debug(f"頁面內容: {response.text[:1000]} ... (省略)")
                return None
            
            law_data = {
                "LawName": law_name,
                "LawCategory": law_category,
                "LawModifiedDate": ''.join(filter(str.isdigit, self._get_text(modified_date_elem))),
                "LawHistories": "",
                "LawArticles": [],
                "LawURL": url
            }
            
            # 獲取法規條文
            article_selectors = ['.row', '.law-article-container', '.law-content']
            
            for selector in article_selectors:
                rows = soup.select(selector)
                if rows:
                    for row in rows:
                        article_no = row.select_one('.col-no a, .article-no')
                        article = row.select_one('.law-article, .article-content')
                        if article_no and article:
                            law_data["LawArticles"].append({
                                "ArticleNo": f"{law_data['LawName']}, {self._get_text(article_no)}",
                                "ArticleContent": self._get_text(article)
                            })
                    if law_data["LawArticles"]:
                        break
            
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
    
    def get_law_urls(self) -> List[str]:
        """
        獲取所有法規的 URL
        
        Returns:
            法規頁面 URL 列表
        """
        category_links, total_laws = self.get_category_links()
        
        if not category_links:
            logging.error("未找到分類連結")
            return []
        
        all_law_urls = []
        for category_url in category_links:
            urls = self.get_law_links(category_url)
            all_law_urls.extend(urls)
            logging.info(f"從 {category_url} 獲取了 {len(urls)} 個法規 URL")
            
            # 為了測試目的，如果找到了一些法規 URL，就提前返回
            if len(all_law_urls) > 0:
                logging.info(f"已找到 {len(all_law_urls)} 個法規 URL，提前返回")
                return all_law_urls
        
        logging.info(f"總共找到 {len(all_law_urls)} 個法規 URL")
        
        # 如果沒有找到任何 URL，嘗試使用緊急方案
        if not all_law_urls:
            logging.warning("找不到任何法規 URL，使用緊急方案")
            emergency_urls = [
                "https://law.moj.gov.tw/LawAll.aspx?PCODE=A0000001",  # 中華民國憲法
                "https://law.moj.gov.tw/LawAll.aspx?PCODE=B0000001",  # 中華民國民法
                "https://law.moj.gov.tw/LawAll.aspx?PCODE=C0000001"   # 中華民國刑法
            ]
            logging.info(f"緊急方案添加了 {len(emergency_urls)} 個法規 URL")
            return emergency_urls
        
        return all_law_urls
    
    def run(self) -> None:
        """
        運行中央法規爬蟲
        """
        law_urls = self.get_law_urls()
        
        if not law_urls:
            logging.error("未找到法規 URL")
            return
            
        logging.info(f"找到 {len(law_urls)} 個法規 URL")
        
        processed_count = self.process_batch(law_urls, self.process_law, "處理法規中")
        
        logging.info(f"完成！成功處理了 {processed_count} 個法規")


if __name__ == "__main__":
    crawler = CentralLawCrawler()
    crawler.run()
