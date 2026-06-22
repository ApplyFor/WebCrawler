from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import csv

# 定義輸出的 CSV 檔案表頭欄位
csv_column = ['教師', '作者', '論文名稱', '會議名稱', '地點']

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
    # 啟動 Chrome 瀏覽器虛擬實例(Instance)
    driver = webdriver.Chrome()

    # 開啟準備儲存結果的 CSV 檔案並寫入表頭
    with open(save_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_column)

        # 遍歷外部輸入的教授名單
        for i, professor in enumerate(professor_list):
            # 第一位教授：先導航至首頁，並定位首頁中央的「全域搜尋框」
            if i == 0:
                driver.get("https://researchoutput.ncku.edu.tw/zh/")
                search = driver.find_element(By.ID, 'global-search-input')
            # 之後的教授：因為頁面結構已變，直接定位上方導覽列的「頂部搜尋框」
            else:
                search = driver.find_element(By.ID, 'main-search')

            # 輸入教授姓名並按下 Enter 鍵送出搜尋
            search.send_keys(professor)
            search.send_keys(Keys.ENTER)
            # time.sleep(2) # 等待網頁渲染

            # 在搜尋結果中，利用 XPath 點擊符合「成大個人學者頁面網址」的教授名稱連結
            results = driver.find_element(By.XPATH, '//a[contains(@href, "https://researchoutput.ncku.edu.tw/zh/persons/")]')
            results.click()
            time.sleep(2)

            # 進入個人頁面後，點擊「研究成果」標籤分頁
            research_page = driver.find_elements(By.XPATH, '//span[contains(@class, "label") and contains(text(), "研究成果")]')
            research_page[0].click()
            time.sleep(2)

            # 定位「會議論文 (Conference contribution)」的連結區塊
            Conference_page = driver.find_elements(By.XPATH, '//a[contains(@class, "portal_link count increment-counter") and contains(@aria-label, "Conference contribution")]')
            # 如果該教授沒有任何會議論文成果，則跳過，直接處理下一位教授
            if len(Conference_page) == 0:
                continue
            else:
                Conference_page[0].click()
                time.sleep(2)
            
            ### 篩選出 2023 年度的會議論文索引 (Index) ###
            idx_list = []
            # 抓取清單頁面中目前載入的所有論文項目節點
            Conferences = driver.find_elements(By.CSS_SELECTOR, '.list-result-item')
            for i, item in enumerate(Conferences):

                conference_info = item.text.split('\n')
                # 狀況一：若該項目的第一行純文字為目標年份 '2023'
                if conference_info[0] == '2023':
                    # 透過 class 名稱取得該項目的尾端索引數字 (例如: 'result-item-0' 解析出 0)
                    class_name = item.get_attribute('class').strip().split('-')[-1]
                    idx_list.append(int(class_name))
                # 狀況二：若遇到年份小於 2023 (因列表通常按時間降序排列，遇到更早的年份代表後面都不符合，可直接中斷)
                elif conference_info[0].isdigit() and int(conference_info[0]) < 2023:
                    break
                # 狀況三：若遇到年份大於 2023 (跳過此項目，繼續往下尋找)
                elif conference_info[0].isdigit() and int(conference_info[0]) > 2023:
                    continue
                # 狀況四：其他非年份數字開頭的例外項目 (預設也加入擷取清單中備用)
                else:
                    class_name = item.get_attribute('class').strip().split('-')[-1]
                    idx_list.append(int(class_name))
            
            print('\n')
            print(professor, idx_list)
            for idx in idx_list:
                write_row = []
                # 重新定位頁面中所有的論文標題連結（因為每一次 driver.back() 後 DOM 都會刷新）
                Conferences = driver.find_elements(By.XPATH, '//h3[contains(@class, "title")]')
                Conferences[idx].click()
                time.sleep(3)

                # 擷取詳細頁面的核心資訊：論文名稱、作者群、會議名稱
                # event_info = driver.find_element(By.XPATH, '//tr[contains(@class, "event")]').find_element(By.XPATH, '//span[contains(@class, "prefix")]').text.strip()
                title = driver.find_element(By.CSS_SELECTOR, 'div.rendering h1 span').text.strip()
                author = driver.find_element(By.XPATH, '//p[contains(@class, "relations persons")]').text.strip()
                # event_info = driver.find_element(By.CSS_SELECTOR, 'tr.event').find_element(By.CSS_SELECTOR, 'td').text.split('\n')
                event_name = driver.find_element(By.XPATH, '//tr[./th[contains(text(), "Conference")]]/td').text.strip()

                # 檢查網頁中是否有提供「國家/地區」的表格欄位資訊
                event_loc = driver.find_elements(By.XPATH, '//tr[./th[contains(text(), "國家/地區")]]/td')
                if len(event_loc) != 0:
                    event_loc = event_loc[0].text.strip()
                else:
                    event_loc = 'None' # 若無提供則填入 None

                # 將該筆論文的所有相關欄位寫入暫存的 List
                write_row.append(professor)
                write_row.append(author)
                write_row.append(title)
                write_row.append(event_name)
                write_row.append(event_loc)

                # 於控制台印出日誌供檢查
                # print('professor :', professor)
                print('author :', author)
                print('title :', title)
                print('event :', event_name)
                print('location :', event_loc)

                # 點擊瀏覽器返回鈕，回到該教授的會議論文清單頁
                driver.back()
                print('------------------------------------')
                
                # 將結構化資料即時寫入 CSV 檔案中
                writer.writerow(write_row)
    # time.sleep(100)
    
    # 當所有教授名單遍歷完畢後，關閉網頁瀏覽器
    driver.close()

if __name__ == '__main__':
    # 設定輸入名單與輸出結果的檔案名稱
    path = 'professor_2.txt'
    save_path = 'output_2.csv'

    # 執行讀取文字檔函式
    professor_list = read_txt(path)
    # print(professor_list)
    # web_crawler(['謝孫源'])

    # 啟動主爬蟲程式
    web_crawler(professor_list, save_path)
