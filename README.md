# NCKU Research Output Crawler (成大研究成果爬蟲)

## 專案簡介

這是一個使用 `Python` 的 `Selenium` 實作的網頁爬蟲工具。主要功能是抓取**國立成功大學學術研發成果網**上特定教授的「2023年度會議論文 (Conference contributions)」資訊。

程式透過 `undetected-chromedriver` 繞過反爬蟲機制，會自動搜尋教授名單、進入個人頁面並過濾出 2023 年的會議論文。執行時會在終端機顯示進度，最後將結果匯出成 CSV 檔。



## 環境與依賴套件 (Prerequisites)

1. **Python 3.7+**
2. **安裝套件**：
```bash
pip install undetected-chromedriver
```
3. **Chrome 版本確認**

程式碼預設對應 Chrome 149 版 (`version_main=149`)：
```python
driver = uc.Chrome(options=options, version_main=149, use_subprocess=True)

```
如果你的 Chrome 不是這個版本，，請直接修改代碼中 `version_main` 的數值。`undetected-chromedriver`套件會自動下載對應的 `ChromeDriver` 。



## 使用方法 (Usage)

1. **準備輸入檔案**
建立一個 UTF-8 編碼的純文字檔（如 professor.txt），每行輸入一位教授姓名（程式會自動過濾頭尾空白）：
```text
教授A
教授B
```

2. **執行程式**
```bash
python web_crawler.py

```

3. **輸入路徑**
程式啟動後，依照終端機提示輸入你的名單路徑和預計輸出的 CSV 路徑。輸入完畢後瀏覽器會自動開啟開始爬蟲。 

4. **取得輸出結果**
執行結束後會產出一份 CSV ，格式如下：
| 教師 | 作者 | 論文名稱 | 會議名稱 | 地點 |
| --- | --- | --- | --- | --- |
| 教授A | 作者A, 作者B... | 論文的完整標題 | 發表會議全名 | 會議舉辦國家/地區 |



## 程式碼架構 (Architecture)

* **搜尋框定位切換 (`foundFlag` )**：
首頁和個人頁面的搜尋框 DOM 結構不同。程式透過 `foundFlag` 判斷：剛開始或查無此人時，抓取首頁中央的搜尋框；若前一次搜尋成功，則直接抓取右上角的導覽列搜尋框，省去退回首頁的時間。

* **等待與容錯機制**：
全域設定 30 秒的動態等待 `(WebDriverWait)` 。如果搜尋送出後等不到頁面載入（Timeout），程式會當作查無此人，印出日誌並跳轉下一位，不會讓整個迴圈崩潰。

* **年份過濾**：
因為網站預設按發表時間「降序排列」，爬取時會判斷：
	* 大於2023 年：跳過 (`continue`)。
	* 小於2023 年：代表後面的資料都太舊了，直接中斷迴圈 (`break`) 節省時間。
	* 2023 年：將該論文的 URL 存入列表。

* **直接存取 URL 提取資料**：
為了避免使用 `driver.back()` 退回上一頁時常遇到的 Stale Element 錯誤，程式改成將收集到的論文網址統一用
 `driver.get()` 直接開啟並擷取詳細資訊。

* **資料淨化（Data Cleaning）**：
	* **發表狀態**：自動裁切掉結尾多餘的年份字元。
	* **地點**：有些論文沒有填寫地點欄位，程式會補獲例外錯誤並填入 `'None'`，以防 CSV 錯位。



## 注意事項與未來優化方向 (Notes & TODOs)

* **請勿調整視窗**：
不要手動縮放或點擊瀏覽器，視窗寬度過窄會觸發 RWD 手機版排版，導致頂部搜尋框被隱藏，引發 `ElementNotInteractableException`報錯。
* **伺服器延遲**：
如果遇到成大網站卡頓，導致 30 秒仍拋出 `TimeoutException` 導致教授被跳過，可手動將 `WebDriverWait(driver, 30)` 的數值調高。
* **Hard-code 年份**：
目前2023 是寫死在程式碼裡的。日後若要查其他年份，建議把這部分改成參數化輸入。
* **防爬限制 (Rate Limiting)**：
如果教授名單過長，連續請求可能會被伺服器暫時阻擋，建議在迴圈之間加入隨機的 time.sleep()。
