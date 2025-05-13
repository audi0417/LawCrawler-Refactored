"""
新北市法規爬蟲模塊
爬取新北市法規資料庫的法規內容
"""

import logging
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.parse import urljoin

from config import NEW_TAIPEI_LAW_CONFIG
from crawler.base_crawler import BaseLawCrawler


class NewTaipeiLawCrawler(BaseLawCrawler):
    """
    新北市法規資料庫爬蟲
    """
    
    def __init__(self):
        """
        初始化新北市法規爬蟲
        """
        super().__init__(NEW_TAIPEI_LAW_CONFIG)
        self.base_url = NEW_TAIPEI_LAW_CONFIG['base_url']
    
    def get_law_links_from_category(self, category_url: str) -> List[Dict[str, str]]:
        """
        從單一類別頁面獲取所有法規連結
        
        Args:
            category_url: 類別頁面URL
            
        Returns:
            法規連結列表，每個元素為包含 'title' 和 'fcode' 的字典
        """
        laws = []
        try:
            response = self.session.get(category_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 從表格中找到所有法規連結
            for link in soup.select("table.tab-list a[href*='FLAWDAT01.aspx']"):
                # 跳過已廢止的法規
                if not link.find_previous("img", src="/images/fei.gif"):
                    href = link.get('href', '')
                    if not href:
                        continue
                        
                    # 從href取得lncode並轉換成fcode格式
                    parts = href.split('lncode=')
                    if len(parts) < 2:
                        continue
                        
                    lncode = parts[1]
                    fcode = lncode.replace('1C', 'C')
                    title = link.text.strip()
                    
                    laws.append({
                        'title': title,
                        'fcode': fcode
                    })
            
            self.random_delay()
            return laws
        except Exception as e:
            logging.error(f"抓取類別頁面 {category_url} 時發生錯誤: {e}")
            return []
    
    def try_get_content(self, url: str, law_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        嘗試從URL獲取法規內容
        
        Args:
            url: 要獲取的URL
            law_info: 法規信息字典
            
        Returns:
            包含法規數據的字典，或失敗時返回None
        """
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 檢查是否包含法規內容
            if not soup.select("table.tab-law01 tr") and not soup.select("table.tab-law tr"):
                return None
                
            law_data = {
                "LawName": law_info['title'],
                "LastModified": "",
                "LawArticles": []
            }

            # 獲取修改日期
            header = soup.select_one("#cph_content_lawheader_law")
            if header:
                date_text = header.text
                if '(' in date_text and ')' in date_text:
                    date_text = date_text.split('(')[1].split(')')[0].strip()
                    law_data["LastModified"] = date_text

            # 嘗試兩種可能的table class獲取法規條文
            articles = soup.select("table.tab-law01 tr") or soup.select("table.tab-law tr")
            for row in articles:
                num = row.select_one(".col-th")
                content = row.select_one(".col-td pre")
                if num and content:
                    law_data["LawArticles"].append({
                        "ArticleNo": num.text.strip(),
                        "ArticleContent": content.text.strip()
                    })

            # 只有在成功獲取條文的情況下返回數據
            return law_data if law_data["LawArticles"] else None
        
        except Exception as e:
            logging.error(f"處理法規 {law_info['title']} 內容時發生錯誤: {e}")
            return None
    
    def get_law_json(self, law_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        獲取並解析法規內容
        
        Args:
            law_info: 包含 'title' 和 'fcode' 的字典
            
        Returns:
            包含法規數據的字典，或失敗時返回None
        """
        # 先嘗試0202格式
        url = f"{self.base_url}Scripts/FLAWDAT0202.aspx?fcode={law_info['fcode']}"
        content = self.try_get_content(url, law_info)
        
        # 若0202失敗則嘗試0201格式
        if not content:
            url = f"{self.base_url}Scripts/FLAWDAT0201.aspx?fcode={law_info['fcode']}"
            content = self.try_get_content(url, law_info)
        
        if content:
            # 添加原始URL
            content["LawURL"] = url
            return content
            
        return None
    
    def get_law_urls(self) -> List[Dict[str, str]]:
        """
        獲取所有法規的資訊
        
        Returns:
            包含法規資訊的字典列表
        """
        # 獲取類別列表
        base_url = f"{self.base_url}Level.aspx"
        categories = []
        try:
            response = self.session.get(base_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.select("ul.level a[href*='Query2.aspx?no=C']"):
                href = link.get('href', '')
                if href:
                    full_url = urljoin(base_url, href)
                    categories.append(full_url)
                    
            logging.info(f"找到 {len(categories)} 個類別")
        except Exception as e:
            logging.error(f"獲取類別列表時出錯: {e}")
            return []
            
        # 獲取所有法規連結
        all_laws = []
        for cat_url in categories:
            try:
                laws = self.get_law_links_from_category(cat_url)
                all_laws.extend(laws)
                logging.info(f"從類別 {cat_url} 中獲取了 {len(laws)} 個法規連結")
            except Exception as e:
                logging.error(f"處理類別 {cat_url} 時出錯: {e}")
                
        logging.info(f"共獲取 {len(all_laws)} 個法規連結")
        return all_laws
    
    def process_law(self, law_info: Dict[str, str]) -> bool:
        """
        處理單個法規資訊
        
        Args:
            law_info: 包含 'title' 和 'fcode' 的字典
            
        Returns:
            處理是否成功
        """
        self.random_delay()
        law_data = self.get_law_json(law_info)
        if law_data and law_data["LawName"]:
            filename = f"{law_data['LawName']}.json"
            self.save_json(law_data, filename)
            return True
        return False
    
    def run(self) -> None:
        """
        運行新北市法規爬蟲
        """
        law_infos = self.get_law_urls()
        
        if not law_infos:
            logging.error("未找到法規連結")
            return
            
        processed_count = self.process_batch(law_infos, self.process_law, "處理新北市法規中")
        
        logging.info(f"完成！成功處理了 {processed_count} / {len(law_infos)} 個法規")


if __name__ == "__main__":
    crawler = NewTaipeiLawCrawler()
    crawler.run()
