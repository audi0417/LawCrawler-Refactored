"""
台中市法規爬蟲專用測試
"""

import unittest
import os
import shutil
import logging
from typing import Dict, List, Any
import json

from crawler.taichung_law_crawler import TaichungLawCrawler
from tests.test_crawlers import BaseCrawlerTest


class TestTaichungLawCrawlerSpecific(unittest.TestCase, BaseCrawlerTest):
    """
    台中市法規爬蟲專用測試
    包含對台中市特有結構的測試
    """
    
    def setUp(self):
        """
        測試前準備
        """
        self.crawler_class = TaichungLawCrawler
        self.source_name = "台中市法規"
        super().setUp()
    
    def test_category_fetching(self):
        """
        測試類別獲取
        """
        print(f"\n測試 {self.source_name} 類別獲取")
        
        categories = self.crawler.get_categories()
        
        # 檢查是否獲取到類別
        self.assertTrue(len(categories) > 0, "應該能獲取到法規類別")
        print(f"成功獲取 {len(categories)} 個類別")
        
        # 打印前3個類別（如果有）
        for i, category in enumerate(categories[:3]):
            print(f"類別 {i+1}: {category}")
    
    def test_law_links_from_category(self):
        """
        測試從類別獲取法規連結
        """
        print(f"\n測試 {self.source_name} 從類別獲取法規連結")
        
        # 先獲取類別
        categories = self.crawler.get_categories()
        if not categories:
            self.fail("無法獲取法規類別")
            return
        
        # 使用第一個類別
        category = categories[0]
        print(f"使用類別: {category}")
        
        # 獲取法規連結
        links = self.crawler.get_law_links_from_category(category)
        
        # 檢查是否獲取到連結
        self.assertTrue(len(links) > 0, f"應該能從類別 {category} 獲取到法規連結")
        print(f"成功獲取 {len(links)} 個法規連結")
        
        # 打印前3個連結（如果有）
        for i, link in enumerate(links[:3]):
            print(f"連結 {i+1}: {link['name']} - {link['url']}")
    
    def test_law_structure(self):
        """
        測試法規結構
        """
        print(f"\n測試 {self.source_name} 法規結構")
        
        # 獲取法規列表
        law_infos = self.crawler.get_law_urls()
        
        if not law_infos:
            self.fail("無法獲取法規列表")
            return
        
        # 使用第一個法規
        law_info = law_infos[0]
        print(f"使用法規: {law_info['name']}")
        
        # 獲取法規內容
        law_data = self.crawler.get_law_json(law_info)
        
        # 檢查法規結構
        self.assertIsNotNone(law_data, "應該能獲取法規數據")
        self.assertTrue("LawName" in law_data, "法規數據應該包含名稱")
        self.assertTrue("LawCategory" in law_data, "法規數據應該包含類別")
        self.assertTrue("LawModifiedDate" in law_data, "法規數據應該包含修改日期")
        self.assertTrue("LawArticles" in law_data, "法規數據應該包含條文")
        self.assertTrue("LawURL" in law_data, "法規數據應該包含URL")
        
        # 保存為JSON檔案以便檢查
        test_dir = "taichung_test_output"
        os.makedirs(test_dir, exist_ok=True)
        filename = f"{test_dir}/test_law_structure.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(law_data, f, ensure_ascii=False, indent=2)
        
        print(f"已將法規結構保存到: {filename}")
        print(f"法規名稱: {law_data['LawName']}")
        print(f"法規類別: {law_data['LawCategory']}")
        print(f"修改日期: {law_data['LawModifiedDate']}")
        print(f"條文數量: {len(law_data['LawArticles'])}")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 執行測試
    unittest.main()
