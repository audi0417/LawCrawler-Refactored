"""
LawCrawler 主入口腳本
提供命令行介面來運行各種法規爬蟲
"""

import argparse
import logging
from typing import List

from crawler.central_law_crawler import CentralLawCrawler
from crawler.taipei_law_crawler import TaipeiLawCrawler


def setup_logging() -> None:
    """
    設置日誌記錄
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('law_crawler.log'),
            logging.StreamHandler()
        ]
    )


def parse_args() -> argparse.Namespace:
    """
    解析命令行參數
    
    Returns:
        解析後的參數
    """
    parser = argparse.ArgumentParser(description='台灣法律條文爬蟲工具')
    
    parser.add_argument(
        '--source', 
        choices=['central', 'taipei', 'all'],
        default='all',
        help='要爬取的法規來源 (默認: all)'
    )
    
    return parser.parse_args()


def main() -> None:
    """
    主函數
    """
    setup_logging()
    args = parse_args()
    
    if args.source in ['central', 'all']:
        logging.info("啟動中央法規爬蟲")
        central_crawler = CentralLawCrawler()
        central_crawler.run()
    
    if args.source in ['taipei', 'all']:
        logging.info("啟動台北市法規爬蟲")
        taipei_crawler = TaipeiLawCrawler()
        taipei_crawler.run()


if __name__ == "__main__":
    main()
