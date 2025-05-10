#!/usr/bin/env python
"""
爬蟲測試執行腳本
提供命令行介面來測試各法規爬蟲
"""

import argparse
import logging
import sys
import unittest
from typing import List, Optional

from tests.test_crawlers import TestCentralLawCrawler, TestTaipeiLawCrawler


def setup_logging() -> None:
    """
    設置日誌記錄
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test.log'),
            logging.StreamHandler()
        ]
    )


def parse_args() -> argparse.Namespace:
    """
    解析命令行參數
    
    Returns:
        解析後的參數
    """
    parser = argparse.ArgumentParser(description='台灣法律條文爬蟲測試工具')
    
    parser.add_argument(
        '--source',
        choices=['central', 'taipei', 'all'],
        default='all',
        help='要測試的法規來源 (默認: all)'
    )
    
    parser.add_argument(
        '--test',
        choices=['urls', 'content', 'save', 'full', 'all'],
        default='all',
        help='要執行的測試類型 (默認: all)'
    )
    
    return parser.parse_args()


def get_test_cases(source: str) -> List[unittest.TestCase]:
    """
    獲取要測試的測試用例
    
    Args:
        source: 法規來源
        
    Returns:
        測試用例列表
    """
    test_cases = []
    
    if source in ['central', 'all']:
        test_cases.append(TestCentralLawCrawler)
    
    if source in ['taipei', 'all']:
        test_cases.append(TestTaipeiLawCrawler)
    
    return test_cases


def get_test_methods(test_type: str) -> List[str]:
    """
    獲取要執行的測試方法名稱
    
    Args:
        test_type: 測試類型
        
    Returns:
        測試方法名稱列表
    """
    methods = []
    
    if test_type in ['urls', 'all']:
        methods.append('test_get_urls')
    
    if test_type in ['content', 'all']:
        methods.append('test_get_law_json')
    
    if test_type in ['save', 'all']:
        methods.append('test_save_json')
    
    if test_type in ['full', 'all']:
        methods.append('test_full_process')
    
    return methods


def run_tests(test_cases: List[unittest.TestCase], test_methods: List[str]) -> bool:
    """
    運行測試
    
    Args:
        test_cases: 測試用例列表
        test_methods: 測試方法名稱列表
        
    Returns:
        測試是否全部通過
    """
    # 創建測試套件
    suite = unittest.TestSuite()
    
    # 添加測試
    for test_case in test_cases:
        for method_name in test_methods:
            suite.addTest(test_case(method_name))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回是否全部通過
    return result.wasSuccessful()


def main() -> int:
    """
    主函數
    
    Returns:
        退出碼，0表示成功，非0表示失敗
    """
    setup_logging()
    args = parse_args()
    
    test_cases = get_test_cases(args.source)
    test_methods = get_test_methods(args.test)
    
    if not test_cases:
        logging.error(f"未找到適合的測試用例: {args.source}")
        return 1
    
    if not test_methods:
        logging.error(f"未找到適合的測試方法: {args.test}")
        return 1
    
    logging.info(f"開始測試: 來源={args.source}, 測試類型={args.test}")
    
    success = run_tests(test_cases, test_methods)
    
    if success:
        logging.info("測試全部通過！")
        return 0
    else:
        logging.error("測試失敗！")
        return 1


if __name__ == "__main__":
    sys.exit(main())
