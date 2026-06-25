# https://steam.oxxostudio.tw/category/python/spider/selenium.html
import undetected_chromedriver as uc
#from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import csv
import time


def read_txt(path):
    """
    讀取包含教授名單的文字檔，並去除每行前後的空白及換行符號。
    """
    content = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            content.append(line.strip())
    return content

def web_crawler(professor_list, save_path):
    """
    遍歷教授名單並抓取 2023 年度的會議論文資訊。
    """
    options = Options()
    #使用proxy伺服器
    #options.add_argument('--proxy-server=ip:port')
    driver = uc.Chrome(options=options, version_main=149, use_subprocess=True)

    """
    # 使瀏覽器不會自動關閉
    options.add_experimental_option("detach", True)
    # 隱藏自動化特徵
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # 偽裝 User-Agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")

    # 啟動 Chrome 瀏覽器虛擬實例(Instance)
    driver = webdriver.Chrome(options=options)

    # 覆蓋 navigator.webdriver 值 (防止被偵測)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
      "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    """

    # 強制最大化視窗，避免搜尋框被 RWD 響應式設計隱藏
    driver.maximize_window()

    kWait = WebDriverWait(driver, 30) # 設定全域等待時間為 30 秒

    # 定義輸出的 CSV 檔案表頭欄位
    kCSVTitle = ['教師', '作者', '論文名稱', '會議名稱', '地點']

    # 開啟準備儲存結果的 CSV 檔案並寫入表頭
    with open(save_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(kCSVTitle)

        # 遍歷外部輸入的教授名單
        for i, professor in enumerate(professor_list):
            # 第一位教授：先導航至首頁，並定位首頁中央的「全域搜尋框」
            if i == 0:
                driver.get("https://researchoutput.ncku.edu.tw/zh/")
                # 加入顯式等待 (Explicit Wait)
                # 最多等 30 秒，一旦 ID 為 'global-search-input' 的元素出現，就立刻往下執行
                search = kWait.until(
                    EC.presence_of_element_located((By.ID, 'global-search-input'))
                )
            # 前一位教授沒有找到的話：定位中央的「全域搜尋框」
            elif foundFlag == 0:
                search = kWait.until(
                    EC.presence_of_element_located((By.ID, 'global-search-input'))
                )
            # 之後的教授：因為頁面結構已變，直接定位上方導覽列的「頂部搜尋框」
            else:
                search = kWait.until(
                    EC.element_to_be_clickable((By.ID, "main-search"))
                )

            # 清空輸入框
            search.clear()
            # 輸入教授姓名
            search.send_keys(professor)
            #按下 Enter 鍵送出搜尋
            search.send_keys(Keys.ENTER)

            # 在搜尋結果中，利用 XPath 點擊符合「成大個人學者頁面網址」的教授名稱連結
            try:
                kWait.until(EC.presence_of_element_located((By.XPATH, '//h2[contains(@class, "section-title") and contains(., "概要")]')))
                results = kWait.until(
                    EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "https://researchoutput.ncku.edu.tw/zh/persons/")]'))
                )
                foundFlag = 1
                results.click()
            except TimeoutException:
                # 如果找不到，這裡會捕獲錯誤，我們就在這裡執行 "跳過" 的邏輯
                foundFlag = 0
                print(f"搜尋不到 {professor} 教授，跳過此人。")
                print('\n')
                continue # 跳過當前迴圈，執行下一個教授

            # 進入個人頁面後，點擊「研究成果」標籤分頁
            research_page = kWait.until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "portal_link btn-primary btn-large btn-content-link") and contains(., "研究成果")]'))
            )
            research_page.click()

            # 定位「會議論文 (Conference contribution)」的連結區塊
            try:
                conference_page = kWait.until(
                    EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "portal_link count increment-counter") and contains(@aria-label, "Conference contribution")]'))
                )
                conference_page.click()
            except TimeoutException:
                print(f" {professor} 教授沒有會議論文，跳過此人。")
                print('\n')
                continue


            # 篩選出 2023 年度的會議論文索引 (Index)
            idx_list = []
            # 篩選出 2023 年度的會議論文網址
            paper_urls = []

            # 抓取清單頁面中目前載入的所有論文項目節點
            conference = kWait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list-result-item'))
            )
            for conf in conference:
                #print('conf:', conf.text.split('\n'))
                # 提取年份資訊，若無法提取則預設為 0
                year_text = conf.text.split('\n')[0].strip()

                # 判斷是否為年份
                if year_text.isdigit():
                    year = int(year_text)
                    # 若遇到年份大於 2023 自動跳過此項目，繼續往下尋找
                    if year > 2023:
                        continue
                    # 若遇到年份小於 2023 (因列表通常按時間降序排列，遇到更早的年份代表後面都不符合，可直接中斷)
                    if year < 2023:
                        break

                if year == 2023:
                    # 透過 class 名稱取得該項目的尾端索引數字 (例如: 'list-result-item-0' 解析出 0)
                    index = conf.get_attribute('class').split('-')[-1]
                    idx_list.append(int(index))

                    # 直接找到該項目裡面的 <a> 標籤，把超連結 href 抽出來存起來
                    link = conf.find_element(By.CSS_SELECTOR, 'h3.title a').get_attribute('href')
                    paper_urls.append(link)

            print(f"professor: {professor} index: {idx_list}")

            """
            for idx in idx_list:
                write_row = []

                # 重新定位頁面中所有的論文標題連結（因為每一次 driver.back() 後 DOM 都會刷新）
                conferences = kWait.until(
                        EC.presence_of_all_elements_located((By.XPATH, '//h3[contains(@class, "title")]'))
                )
                kWait.until(EC.element_to_be_clickable(conferences[idx]))
                conferences[idx].click()
                
                # 等待進入論文詳細頁後，確保標題元素已載入，避免抓到舊頁面資訊
                kWait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.rendering h1 span')))

                # 擷取詳細頁面的核心資訊：論文名稱、作者群、會議名稱
                title = driver.find_element(By.CSS_SELECTOR, 'div.rendering h1 span').text.strip()
                author = driver.find_element(By.XPATH, '//ul[contains(@class, "relations persons")]').text.strip()
                publication_status = driver.find_element(By.XPATH, '//tr[contains(@class, "status")]').find_element(By.XPATH, './/span[contains(@class, "prefix")]').text.split("-")[0].strip()
                event_info = driver.find_element(By.CSS_SELECTOR, 'tr.event').find_element(By.CSS_SELECTOR, 'td').text.split('\n')
                event_name = driver.find_element(By.XPATH, '//tr[./th[contains(text(), "Conference")]]/td').text.strip()

                # 檢查網頁中是否有提供「國家/地區」的表格欄位資訊
                try:
                    event_location = driver.find_element(By.XPATH, '//tr[./th[contains(text(), "國家/地區")]]/td')
                    event_location = event_location.text.strip()
                except NoSuchElementException:
                    event_location = 'None' # 若無提供則填入 None

                # 將該筆論文的所有相關欄位寫入暫存的 List
                write_row.append(professor)
                write_row.append(author)
                write_row.append(title)
                write_row.append(event_name)
                write_row.append(event_location)

                # 於控制台印出日誌供檢查
                print('title :', title)
                print('author :', author)
                print('publication_status:', publication_status)
                print('event_info:', event_info)
                print('event :', event_name)
                print('location :', event_location)
                print('------------------------------------')

                # 點擊瀏覽器返回鈕，回到該教授的會議論文清單頁
                driver.back()
                
                # 將結構化資料即時寫入 CSV 檔案中
                writer.writerow(write_row)
            """

            for url in paper_urls:
                write_row = []
                
                # 用 driver.get() 直接進入論文詳細頁，取代點擊與 back()
                driver.get(url)

                # 等待進入論文詳細頁後，確保標題元素已載入
                kWait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.rendering h1 span')))

                title = driver.find_element(By.CSS_SELECTOR, 'div.rendering h1 span').text.strip()
                author = driver.find_element(By.XPATH, '//ul[contains(@class, "relations persons")]').text.strip()
                publication_status = driver.find_element(By.XPATH, '//tr[contains(@class, "status")]').find_element(By.XPATH, './/span[contains(@class, "prefix")]').text.split("-")[0].strip()
                event_info = driver.find_element(By.CSS_SELECTOR, 'tr.event').find_element(By.CSS_SELECTOR, 'td').text.split('\n')
                event_name = driver.find_element(By.XPATH, '//tr[./th[contains(text(), "Conference")]]/td').text.strip()
                
                try:
                    event_location = driver.find_element(By.XPATH, '//tr[./th[contains(text(), "國家/地區")]]/td')
                    event_location = event_location.text.strip()
                except NoSuchElementException:
                    event_location = 'None'

                write_row.append(professor)
                write_row.append(author)
                write_row.append(title)
                write_row.append(event_name)
                write_row.append(event_location)

                print('title :', title)
                print('author :', author)
                print('publication_status:', publication_status)
                print('event_info:', event_info)
                print('event :', event_name)
                print('location :', event_location)
                print('------------------------------------')
                
                writer.writerow(write_row)
            print('\n')
        # time.sleep(120)
    
    # 當所有教授名單遍歷完畢後，關閉網頁瀏覽器
    driver.close()

if __name__ == '__main__':
    
    # 設定輸入名單與輸出結果的檔案名稱
    path = 'input/professor.txt'
    save_path = 'output/output.csv'
    """
    #path = input('輸入名單的檔案路徑：')
    #save_path = input('輸出結果的檔案路徑：')
    """

    # 執行讀取文字檔函式
    professor_list = read_txt(path)
    # print(professor_list)

    # 啟動主爬蟲程式
    # web_crawler(['謝孫源'], 'output/test.csv')
    web_crawler(professor_list, save_path)
