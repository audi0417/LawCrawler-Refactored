"""
台中市法規爬蟲模塊
爬取台中市法規資料庫的法規內容
"""

import logging
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.parse import urljoin

from config import TAICHUNG_LAW_CONFIG
from crawler.base_crawler import BaseLawCrawler


class TaichungLawCrawler(BaseLawCrawler):
    """
    台中市法規資料庫爬蟲
    """
    
    def __init__(self):
        """
        初始化台中市法規爬蟲
        """
        super().__init__(TAICHUNG_LAW_CONFIG)
        self.base_url = TAICHUNG_LAW_CONFIG['base_url']
    
    def get_categories(self) -> List[str]:
        """
        獲取所有法規類別連結
        
        Returns:
            類別URL列表
        """
        category_base_url = f"{self.base_url}LawCategoryMain.aspx"
        try:
            response = self.session.get(category_base_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            category_links = []
            
            # 找出所有類別連結
            for link in soup.select("a[href*='LawCategoryMain.aspx?CategoryID=']"):
                href = link.get('href', '')
                if href and 'CategoryID=' in href:
                    full_url = urljoin(self.base_url, href)
                    category_links.append(full_url)
            
            logging.info(f"找到 {len(category_links)} 個類別")
            return category_links
            
        except Exception as e:
            logging.error(f"獲取類別時出錯: {e}")
            return []
    
    def get_law_links_from_category(self, category_url: str) -> List[Dict[str, str]]:
        """
        從單一類別頁面獲取所有法規連結
        
        Args:
            category_url: 類別頁面URL
            
        Returns:
            法規連結列表，每個元素為包含 'url' 和 'name' 的字典
        """
        all_links = []
        page = 1
        
        while True:
            url = f"{category_url}&page={page}" if '?' in category_url else f"{category_url}?page={page}"
            
            try:
                self.random_delay()
                response = self.session.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                rows = soup.select("table.table-hover tr")
                if not rows:
                    break
                    
                for row in rows:
                    # 跳過已廢除的法規
                    if row.select_one("span.label-fei"):
                        continue
                        
                    link = row.select_one("a[href*='LawContent.aspx']")
                    if link and link.get('href'):
                        full_url = urljoin(self.base_url, link['href'])
                        name = link.text.strip()
                        
                        all_links.append({
                            'url': full_url,
                            'name': name
                        })
                
                # 檢查是否有下一頁
                next_page = soup.select_one(f"a[href*='page={page + 1}']")
                if not next_page:
                    break
                    
                page += 1
                
            except Exception as e:
                logging.error(f"從類別頁面獲取法規連結時出錯 (頁碼 {page}): {e}")
                break
                
        return all_links
    
    def get_law_urls(self) -> List[Dict[str, str]]:
        """
        獲取所有法規頁面的URL及名稱
        
        Returns:
            法規頁面URL及名稱的列表
        """
        all_law_links = []
        categories = self.get_categories()
        
        for category_url in categories:
            try:
                links = self.get_law_links_from_category(category_url)
                all_law_links.extend(links)
                logging.info(f"從類別 {category_url} 中獲取了 {len(links)} 個法規連結")
            except Exception as e:
                logging.error(f"處理類別 {category_url} 時出錯: {e}")
        
        logging.info(f"共獲取 {len(all_law_links)} 個法規連結")
        return all_law_links
    
    def get_law_json(self, law_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        解析單一法規內容
        
        Args:
            law_info: 包含 'url' 和 'name' 的字典
            
        Returns:
            包含法規數據的字典，或在失敗時返回 None
        """
        try:
            self.random_delay()
            url = law_info['url']
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 基本資料表格
            info_table = soup.select_one("table.table-bordered")
            
            law_data = {
                "LawName": law_info['name'],
                "LawCategory": "",
                "LawModifiedDate": "",
                "LawArticles": [],
                "LawURL": url
            }
            
            if info_table:
                # 取得基本資料
                rows = info_table.select("tr")
                for row in rows:
                    th = row.select_one("th")
                    td = row.select_one("td")
                    if not th or not td:
                        continue
                        
                    th_text = th.text.strip()
                    td_text = td.text.strip()
                    
                    if "法規名稱" in th_text:
                        law_data["LawName"] = td_text
                    elif "法規體系" in th_text:
                        law_data["LawCategory"] = td_text
                    elif "公發布日" in th_text or "修正日期" in th_text:
                        law_data["LawModifiedDate"] = td_text
            
            # 取得法規內容
            content_table = soup.select_one("table.tab-law")
            if content_table:
                for row in content_table.select("tr"):
                    td = row.select_one("td:nth-of-type(2)")
                    number = row.select_one("td:nth-of-type(1)")
                    
                    if td and number:
                        content = td.text.strip()
                        article_number = number.text.strip()
                        
                        if content:
                            law_data["LawArticles"].append({
                                "ArticleNo": article_number,
                                "ArticleContent": content
                            })
            
            return law_data
        except Exception as e:
            logging.error(f"處理 URL {url} 時出錯: {e}")
            return None
    
    def process_law(self, law_info: Dict[str, str]) -> bool:
        """
        處理單個法規連結
        
        Args:
            law_info: 包含 'url' 和 'name' 的字典
            
        Returns:
            處理是否成功
        """
        law_data = self.get_law_json(law_info)
        if law_data and law_data["LawName"]:
            filename = f"{law_data['LawName']}.json"
            self.save_json(law_data, filename)
            return True
        return False
    
    def run(self) -> None:
        """
        運行台中市法規爬蟲
        """
        law_infos = self.get_law_urls()
        
        if not law_infos:
            logging.error("未找到法規連結")
            return
            
        processed_count = self.process_batch(law_infos, self.process_law, "處理台中市法規中")
        
        logging.info(f"完成！成功處理了 {processed_count} / {len(law_infos)} 個法規")


if __name__ == "__main__":
    crawler = TaichungLawCrawler()
    crawler.run()
