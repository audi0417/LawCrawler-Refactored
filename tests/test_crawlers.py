"""
爬蟲測試腳本
提供單元測試及集成測試功能
"""

import unittest
import os
import shutil
import logging
from typing import Any, Dict, List, Type

from crawler.base_crawler import BaseLawCrawler
from crawler.central_law_crawler import CentralLawCrawler
from crawler.taipei_law_crawler import TaipeiLawCrawler
from crawler.new_taipei_law_crawler import NewTaipeiLawCrawler
from crawler.taichung_law_crawler import TaichungLawCrawler
from crawler.taoyuan_law_crawler import TaoyuanLawCrawler
from crawler.kaohsiung_law_crawler import KaohsiungLawCrawler


class BaseCrawlerTest:
    """
    爬蟲基礎測試類，不應直接實例化
    """
    
    crawler_class: Type[BaseLawCrawler] = None
    source_name: str = ""
    
    def setUp(self):
        """
        測試前準備
        """
        if not self.crawler_class:
            raise ValueError("測試類必須設置 crawler_class 屬性")
            
        self.crawler = self.crawler_class()
        
        # 設置測試配置
        self.crawler.config['max_workers'] = 2
        self.crawler.config['batch_size'] = 1
        
        # 確保輸出目錄不存在
        if os.path.exists(self.crawler.config['output_dir']):
            shutil.rmtree(self.crawler.config['output_dir'])
    
    def test_get_urls(self):
        """
        測試獲取法規URL列表
        """
        print(f"\n測試 {self.source_name} 法規獲取URL")
        
        if hasattr(self.crawler, 'get_law_urls'):
            urls = self.crawler.get_law_urls()
            self.assertTrue(len(urls) > 0, f"應該能獲取到 {self.source_name} 法規URL")
            print(f"成功獲取 {len(urls)} 個 {self.source_name} 法規URL")
            
            # 返回前3個URL用於後續測試
            return urls[:3]
        else:
            self.fail(f"{self.source_name} 爬蟲沒有實現 get_law_urls 方法")
    
    def test_get_law_json(self):
        """
        測試獲取法規內容
        """
        print(f"\n測試 {self.source_name} 法規內容抓取")
        
        # 獲取URL
        urls = self.test_get_urls()
        
        # 測試每個URL
        for url in urls:
            print(f"測試URL: {url}")
            law_data = self.crawler.get_law_json(url)
            
            # 檢查是否成功獲取數據
            self.assertIsNotNone(law_data, f"應該能從 {url} 獲取法規數據")
            self.assertTrue("LawName" in law_data, "法規數據應該包含名稱")
            self.assertTrue("LawArticles" in law_data, "法規數據應該包含條文")
            
            # 打印法規名稱
            print(f"成功獲取法規: {law_data['LawName']}")
    
    def test_save_json(self):
        """
        測試保存為JSON
        """
        print(f"\n測試 {self.source_name} 法規保存為JSON")
        
        # 獲取URL
        urls = self.test_get_urls()
        
        # 只測試第一個URL
        if urls:
            url = urls[0]
            print(f"測試URL: {url}")
            
            # 獲取法規內容
            law_data = self.crawler.get_law_json(url)
            
            # 保存為JSON
            if law_data and "LawName" in law_data:
                filename = f"{law_data['LawName']}.json"
                self.crawler.save_json(law_data, filename)
                
                # 檢查文件是否存在
                filepath = os.path.join(self.crawler.config['output_dir'], filename)
                self.assertTrue(os.path.exists(filepath), f"應該能保存法規為JSON: {filepath}")
                print(f"成功保存法規為JSON: {filepath}")
            else:
                self.fail(f"無法獲取有效的法規數據")
    
    def test_full_process(self):
        """
        測試完整流程
        """
        print(f"\n測試 {self.source_name} 爬蟲完整流程")
        
        # 獲取URL並限制數量
        if hasattr(self.crawler, 'get_law_urls'):
            urls = self.crawler.get_law_urls()
            urls = urls[:3]  # 只處理前3個
            
            # 處理法規
            processed_count = 0
            for url in urls:
                try:
                    # 提取並保存法規
                    law_data = self.crawler.get_law_json(url)
                    if law_data and "LawName" in law_data:
                        filename = f"{law_data['LawName']}.json"
                        self.crawler.save_json(law_data, filename)
                        processed_count += 1
                except Exception as e:
                    print(f"處理URL失敗: {url}, 錯誤: {e}")
            
            # 檢查是否有處理成功的法規
            self.assertTrue(processed_count > 0, f"應該至少成功處理一個法規")
            print(f"成功處理 {processed_count} 個法規")
            
            # 列出所有保存的文件
            output_dir = self.crawler.config['output_dir']
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                print(f"輸出目錄 {output_dir} 中有 {len(files)} 個文件:")
                for file in files:
                    print(f"  - {file}")
        else:
            self.fail(f"{self.source_name} 爬蟲沒有實現 get_law_urls 方法")


class TestCentralLawCrawler(unittest.TestCase, BaseCrawlerTest):
    """
    中央法規爬蟲測試
    """
    
    def setUp(self):
        self.crawler_class = CentralLawCrawler
        self.source_name = "中央法規"
        super().setUp()


class TestTaipeiLawCrawler(unittest.TestCase, BaseCrawlerTest):
    """
    台北市法規爬蟲測試
    """
    
    def setUp(self):
        self.crawler_class = TaipeiLawCrawler
        self.source_name = "台北市法規"
        super().setUp()


class TestNewTaipeiLawCrawler(unittest.TestCase, BaseCrawlerTest):
    """
    新北市法規爬蟲測試
    """
    
    def setUp(self):
        self.crawler_class = NewTaipeiLawCrawler
        self.source_name = "新北市法規"
        super().setUp()


class TestTaichungLawCrawler(unittest.TestCase, BaseCrawlerTest):
    """
    台中市法規爬蟲測試
    """
    
    def setUp(self):
        self.crawler_class = TaichungLawCrawler
        self.source_name = "台中市法規"
        super().setUp()


class TestTaoyuanLawCrawler(unittest.TestCase, BaseCrawlerTest):
    """
    桃園市法規爬蟲測試
    """
    
    def setUp(self):
        self.crawler_class = TaoyuanLawCrawler
        self.source_name = "桃園市法規"
        super().setUp()


class TestKaohsiungLawCrawler(unittest.TestCase, BaseCrawlerTest):
    """
    高雄市法規爬蟲測試
    """
    
    def setUp(self):
        self.crawler_class = KaohsiungLawCrawler
        self.source_name = "高雄市法規"
        super().setUp()


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 執行測試
    unittest.main()
