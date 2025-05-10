"""
基礎爬蟲類
包含所有爬蟲共用的功能
"""

import os
import json
import time
import random
import logging
import requests
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import HEADERS, RETRY_CONFIG


class BaseLawCrawler:
    """
    法規爬蟲的基礎類，提供共用功能
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化爬蟲
        
        Args:
            config: 爬蟲配置字典，應包含 output_dir, log_file 等
        """
        self.config = config
        self.session = self._create_session()
        self._setup_logging()
    
    def _create_session(self) -> requests.Session:
        """
        創建並配置 HTTP 會話
        
        Returns:
            配置好的 requests.Session 對象
        """
        session = requests.Session()
        retry = Retry(
            total=RETRY_CONFIG['total'],
            backoff_factor=RETRY_CONFIG['backoff_factor'],
            status_forcelist=RETRY_CONFIG['status_forcelist']
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update(HEADERS)
        return session
    
    def _setup_logging(self) -> None:
        """
        設置日誌記錄
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['log_file']),
                logging.StreamHandler()
            ]
        )
    
    def save_json(self, data: Dict[str, Any], filename: str) -> None:
        """
        將數據保存為 JSON 文件
        
        Args:
            data: 要保存的數據字典
            filename: 文件名
        """
        os.makedirs(self.config['output_dir'], exist_ok=True)
        filepath = os.path.join(self.config['output_dir'], filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def random_delay(self) -> None:
        """
        隨機延遲，避免請求過於頻繁
        """
        time.sleep(random.uniform(
            self.config['delay_min'], 
            self.config['delay_max']
        ))
    
    def process_batch(
        self, 
        urls: List[str], 
        process_func, 
        desc: str = "Processing"
    ) -> int:
        """
        批量處理 URL
        
        Args:
            urls: URL 列表
            process_func: 處理單個 URL 的函數
            desc: 進度條描述
            
        Returns:
            成功處理的項目數量
        """
        processed_count = 0
        
        with tqdm(total=len(urls), desc=desc) as pbar:
            for i in range(0, len(urls), self.config['batch_size']):
                batch = urls[i:i+self.config['batch_size']]
                
                with ThreadPoolExecutor(max_workers=self.config['max_workers']) as executor:
                    futures = [executor.submit(process_func, url) for url in batch]
                    
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            if result:
                                processed_count += 1
                        except Exception as e:
                            logging.error(f"Error processing item: {e}")
                        pbar.update(1)
        
        return processed_count
    
    def run(self) -> None:
        """
        運行爬蟲，子類必須實現此方法
        """
        raise NotImplementedError("Subclasses must implement run()")
