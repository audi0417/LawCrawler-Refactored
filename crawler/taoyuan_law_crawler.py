"""
桃園市法規爬蟲模塊
爬取桃園市法規資料庫的法規內容
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.parse import urljoin

from config import TAOYUAN_LAW_CONFIG
from crawler.base_crawler import BaseLawCrawler


class TaoyuanLawCrawler(BaseLawCrawler):
    """
    桃園市法規資料庫爬蟲
    """
    
    def __init__(self):
        """
        初始化桃園市法規爬蟲
        """
        super().__init__(TAOYUAN_LAW_CONFIG)
        self.base_url = TAOYUAN_LAW_CONFIG['base_url']
    
    def get_all_laws_url(self) -> Tuple[Optional[str], int]:
        """
        獲取所有法規的URL
        
        Returns:
            (所有法規的URL, 法規總數)
        """
        try:
            # 直接使用"全部"法規的URL
            all_laws_url = urljoin(self.base_url, "LawResultList.aspx?NLawTypeID=all&GroupID=&CategoryID=1%2c01%2c02%2c03%2c04%2c05%2c06%2c07%2c08%2c09%2c10%2c11%2c12%2c13%2c14%2c15%2c16%2c17%2c18%2c19%2c20%2c21%2c22%2c23%2c24%2c25%2c26%2c27%2c28%2c29%2c30%2c31%2c33%2c34%2c35%2c36%2c32%2cb01%2cb02%2cb03%2cb04%2cb05%2cb06%2cb07%2cb08%2cb09%2cb10%2cb11%2cb12%2c&KW=&name=1&content=1&StartDate=&EndDate=&LNumber=&now=1&fei=1")
            
            response = self.session.get(all_laws_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 從頁面獲取總法規數
            page_info = soup.select_one(".pageinfo")
            total_laws = 0
            if page_info:
                info_text = page_info.text
                if "共" in info_text and "筆" in info_text:
                    try:
                        total_laws = int(info_text.split("共")[1].split("筆")[0].strip())
                        logging.info(f"總法規數: {total_laws}")
                    except:
                        logging.warning("無法解析法規總數")
            
            return all_laws_url, total_laws
            
        except Exception as e:
            logging.error(f"獲取所有法規URL時出錯: {e}")
            return None, 0
    
    def get_law_links_from_page(self, url: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        從單一頁面獲取所有法規連結
        
        Args:
            url: 頁面URL
            
        Returns:
            (法規連結列表, 下一頁URL)
        """
        try:
            self.random_delay()
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            law_links = []
            
            # 獲取當前頁面的所有法規連結
            rows = soup.select("table.table-hover tr")
            for row in rows:
                # 跳過已廢止的法規
                if row.select_one(".label-fei"):
                    continue
                
                link = row.select_one("a[href*='LawContent.aspx']")
                if link and link.get('href'):
                    full_url = urljoin(self.base_url, link['href'])
                    date_td = row.select_one("td:nth-of-type(2)")
                    date = date_td.text.strip() if date_td else ""
                    
                    law_links.append({
                        'url': full_url,
                        'name': link.text.strip(),
                        'date': date
                    })
            
            # 查找下一頁連結
            next_page = soup.select_one("a#ctl00_cp_content_rptList_ctl11_PagerButtom_hlNext")
            next_page_url = None
            if next_page and 'disabled' not in next_page.get('class', []) and next_page.get('href'):
                next_page_url = urljoin(self.base_url, next_page['href'])
            
            return law_links, next_page_url
            
        except Exception as e:
            logging.error(f"獲取頁面 {url} 法規連結時出錯: {e}")
            return [], None
    
    def get_law_urls(self) -> List[Dict[str, str]]:
        """
        獲取所有法規頁面的URL及相關信息
        
        Returns:
            包含 'url', 'name', 'date' 的字典列表
        """
        all_links = []
        start_url, total_laws = self.get_all_laws_url()
        
        if not start_url:
            logging.error("無法獲取法規列表URL")
            return all_links
            
        current_url = start_url
        page = 1
        
        while current_url:
            logging.info(f"處理第 {page} 頁: {current_url}")
            links, next_url = self.get_law_links_from_page(current_url)
            all_links.extend(links)
            
            if not next_url:
                break
                
            current_url = next_url
            page += 1
        
        logging.info(f"從 {page} 頁中找到 {len(all_links)} 個法規連結")
        return all_links
    
    def get_law_json(self, law_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        解析單一法規內容頁面
        
        Args:
            law_info: 包含 'url', 'name', 'date' 的字典
            
        Returns:
            包含法規數據的字典，或失敗時返回None
        """
        try:
            self.random_delay()
            response = self.session.get(law_info['url'])
            soup = BeautifulSoup(response.text, 'html.parser')
            
            law_data = {
                "LawName": law_info['name'],
                "LawURL": law_info['url'],
                "LawDate": law_info.get('date', ''),
                "LawType": "",
                "LawCategory": "",
                "LawPublishDate": "",
                "LawModifiedDate": "",
                "LawArticles": []
            }
            
            # 獲取法規基本資訊
            info_table = soup.select_one("table.table-bordered")
            if info_table:
                for row in info_table.select("tr"):
                    th = row.select_one("th")
                    td = row.select_one("td")
                    if not th or not td:
                        continue
                    
                    field_name = th.text.strip()
                    field_value = td.text.strip()
                    
                    if "法規名稱" in field_name:
                        law_data["LawName"] = field_value
                    elif "法規體系" in field_name:
                        law_data["LawCategory"] = field_value
                    elif "公發布日" in field_name:
                        law_data["LawPublishDate"] = field_value
                    elif "修正日期" in field_name:
                        law_data["LawModifiedDate"] = field_value
                    elif "發文字號" in field_name:
                        law_data["LawNumber"] = field_value
            
            # 獲取法規條文內容
            law_content_table = soup.select_one("table.tab-law")
            if law_content_table:
                for row in law_content_table.select("tr"):
                    cols = row.select("td")
                    if len(cols) >= 2:
                        article_number = cols[0].text.strip()
                        article_content = cols[1].text.strip()
                        
                        if article_content:
                            law_data["LawArticles"].append({
                                "ArticleNo": article_number,
                                "ArticleContent": article_content
                            })
                    elif len(cols) == 1 and "章" in cols[0].text:
                        # 這是章節標題
                        chapter_title = cols[0].text.strip()
                        law_data["LawArticles"].append({
                            "ArticleNo": "章節",
                            "ArticleContent": chapter_title
                        })
            
            # 如果沒有找到條文表格，嘗試從其他地方獲取內容
            if not law_data["LawArticles"]:
                content_div = soup.select_one(".law-reg-content")
                if content_div:
                    law_data["LawArticles"].append({
                        "ArticleNo": "",
                        "ArticleContent": content_div.text.strip()
                    })
            
            return law_data
            
        except Exception as e:
            logging.error(f"處理法規 {law_info['name']} 時出錯: {e}")
            return None
    
    def process_law(self, law_info: Dict[str, str]) -> bool:
        """
        處理單個法規
        
        Args:
            law_info: 包含 'url', 'name', 'date' 的字典
            
        Returns:
            處理是否成功
        """
        law_data = self.get_law_json(law_info)
        if law_data and law_data["LawName"]:
            # 處理檔名中可能有的特殊字元
            safe_filename = "".join([c for c in law_data["LawName"] if c.isalnum() or c in ' _-']).strip()
            if not safe_filename:
                safe_filename = f"law_{hash(law_data['LawName']) % 10000}"
                
            filename = f"{safe_filename}.json"
            self.save_json(law_data, filename)
            return True
        return False
    
    def run(self) -> None:
        """
        運行桃園市法規爬蟲
        """
        law_infos = self.get_law_urls()
        
        if not law_infos:
            logging.error("未找到法規連結")
            return
            
        processed_count = self.process_batch(law_infos, self.process_law, "處理桃園市法規中")
        
        logging.info(f"完成！成功處理了 {processed_count} / {len(law_infos)} 個法規")


if __name__ == "__main__":
    crawler = TaoyuanLawCrawler()
    crawler.run()
