"""
爬蟲配置文件
包含不同法規爬蟲的配置參數
"""

# HTTP 請求頭
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive'
}

# 中央法規爬蟲配置
CENTRAL_LAW_CONFIG = {
    'base_url': 'https://law.moj.gov.tw/Law/',
    'search_url': 'LawSearchLaw.aspx',
    'output_dir': 'law_jsons',
    'log_file': 'central_laws_crawler.log',
    'max_workers': 5,
    'batch_size': 20,
    'delay_min': 1,
    'delay_max': 2
}

# 台北市法規爬蟲配置
TAIPEI_LAW_CONFIG = {
    'base_url': 'https://www.laws.taipei.gov.tw',
    'category_url': 'Law/LawCategory/LawCategoryResult?categoryid=001&page={}',
    'output_dir': 'taipei_law_jsons',
    'log_file': 'taipei_laws_crawler.log',
    'max_workers': 5,
    'batch_size': 20,
    'delay_min': 1,
    'delay_max': 2
}

# 新北市法規爬蟲配置
NEW_TAIPEI_LAW_CONFIG = {
    'base_url': 'https://web.law.ntpc.gov.tw/',
    'output_dir': 'new_taipei_law_jsons',
    'log_file': 'new_taipei_laws_crawler.log',
    'max_workers': 5,
    'batch_size': 20,
    'delay_min': 1,
    'delay_max': 2
}

# 台中市法規爬蟲配置
TAICHUNG_LAW_CONFIG = {
    'base_url': 'https://law.taichung.gov.tw/',
    'output_dir': 'taichung_law_jsons',
    'log_file': 'taichung_laws_crawler.log',
    'max_workers': 5,
    'batch_size': 20,
    'delay_min': 1,
    'delay_max': 2
}

# 桃園市法規爬蟲配置
TAOYUAN_LAW_CONFIG = {
    'base_url': 'https://law.tycg.gov.tw/',
    'output_dir': 'taoyuan_law_jsons',
    'log_file': 'taoyuan_laws_crawler.log',
    'max_workers': 5,
    'batch_size': 20,
    'delay_min': 1,
    'delay_max': 2
}

# 高雄市法規爬蟲配置
KAOHSIUNG_LAW_CONFIG = {
    'base_url': 'https://outlaw.kcg.gov.tw/',
    'output_dir': 'kaohsiung_law_jsons',
    'log_file': 'kaohsiung_laws_crawler.log',
    'max_workers': 5,
    'batch_size': 20,
    'delay_min': 1,
    'delay_max': 2
}

# HTTP 重試配置
RETRY_CONFIG = {
    'total': 3,
    'backoff_factor': 0.5,
    'status_forcelist': [500, 502, 503, 504]
}
