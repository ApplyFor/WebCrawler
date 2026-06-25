# NCKU Research Output Crawler (成大研究成果爬蟲)

## 專案簡介

這是一個基於 `Python` 的 `Selenium` 自動化套件實作的網頁自動化爬蟲專案。主要用途為自動擷取**國立成功大學 (NCKU) 學術研發成果網**上特定教授的「2023年度會議論文 (Conference contributions)」資訊。

透過批次讀取教授名單，系統會利用 `undetected-chromedriver`（反偵測 Chrome 驅動）繞過自動化特徵審查，自動化開啟瀏覽器、搜尋教授、進入其研究成果頁面，並精準過濾出 2023 年度的會議論文，同時於終端機印出詳細日誌，以供您在執行期間即時監控爬取進度。

最後將每篇論文的詳細資訊結構化並匯出為 CSV 檔案，以利後續的學術表現統計與數據分析。



## 環境與依賴套件 (Prerequisites)

在執行本專案前，請確保您的環境滿足以下條件：

1. Python 3.7+
2. 爬蟲核心與反偵測套件：
```bash
pip install undetected-chromedriver
```
3. Chrome 瀏覽器版本對齊

程式碼指定使用 **Chrome 大版本號 149** (`version_main=149`)：

```python
driver = uc.Chrome(options=options, version_main=149, use_subprocess=True)

```

請確保所安裝的 Google Chrome 瀏覽器主版本號與此設定一致。若版本不同，請直接修改代碼中 `version_main` 的數值。`undetected-chromedriver`套件會根據此設定自動下載並管理對應的 `ChromeDriver` 檔案。



## 使用方法 (Usage)

1. **準備輸入檔案**
在您方便的路徑下建立一個純文字檔（如 `professor.txt`）（ UTF-8 編碼），並以 UTF-8 編碼儲存。
將需要查詢的教授姓名**逐行寫入**，程式內建的函式會自動去除每行前後的髒空白與換行符號：
```text
教授A
教授B
```

2. **執行腳本**
在終端機 (Terminal) 中執行以下指令啟動程式：
```bash
python web_crawler.py

```
*(執行期間 Chrome 瀏覽器會自動開啟並進行網頁操作，請勿手動關閉或干擾瀏覽器視窗)*

3. **輸入路徑參數**
程式啟動後，終端機會出現提示文字，請依序輸入您的檔案路徑（可使用相對路徑或絕對路徑）：

輸入名單的檔案路徑： (例如：`professor.txt` 或 `C:/data/list.txt`)

輸出結果的檔案路徑： (例如：`output.csv` 或 `result/2023_papers.csv`)

輸入完畢按下 Enter 後，Chrome 瀏覽器便會自動開啟並開始爬取。 

4. **取得輸出結果**
程式執行完畢後，會自動關閉瀏覽器，並在指定的輸出路徑生成 `csv` 檔案，資料格式如下：
| 教師 | 作者 | 論文名稱 | 會議名稱 | 地點 |
| --- | --- | --- | --- | --- |
| 教授A | 作者A, 作者B... | 論文的完整標題 | 發表會議全名 | 會議舉辦國家/地區 |



## 程式碼架構 (Architecture)

* **智慧狀態型搜尋框定位 (`foundFlag` 機制)**：
為了應對動態網頁在不同狀態下的 DOM 結構改變，程式實作了狀態判定：
	* **初始輪 (`i == 0`)**：直接載入成大研發成果網首頁，定位中央的 `global-search-input` 搜尋框。
	* **查無此人後 (`foundFlag == 0`)**：若前一位教授未成功找到，頁面會停留在錯誤或初始狀態，繼續定位中央的 `global-search-input`搜尋框。
	* **連續搜尋 (`foundFlag == 1`)**：若成功進入前一位教授的學者頁面，此時頁面頂部已出現常駐導覽列，程式改為自動定位右上角的 `main-search` 搜尋框，實現不跳轉首頁的連續檢索。

* **多重顯式等待與容錯 (`kWait`)**：
全域採用 `WebDriverWait(driver, 30)` 進行 30 秒的動態顯式等待。
	* 搜尋送出後，強制驗證頁面是否載入包含「概要」文字的節點，隨後定位學者個人頁面網址。
	* 若搜尋超時（觸發 `TimeoutException`），代表查無此人，程式會將 `foundFlag` 歸零、印出日誌並透過 `continue` 安全跳過，不影響後續名單。

* **過濾年份**：
進入會議論文清單頁面（`.list-result-item`）後，由於網站預設採取發表時間「降序排列」：
	* 若年份大於 2023 年：執行 `continue` 略過。
	* 若年份小於 2023 年：執行 `break` 直接中斷迴圈，不再浪費時間讀取後續的過期資料。
	* 若年份剛好等於 2023 年：同時記錄清單尾端的 `index` 數值並抽取出該論文的真實 URL (href) 存入 `paper_urls` 列表中。

* **無狀態 (Stateless) URL 提取**：
完全捨棄了傳統動態爬蟲中極易因 DOM 刷新而崩潰的 `driver.back()` 點擊模式，直接遍歷收集到的 `paper_urls`。
每筆論文皆使用 `driver.get(url)` 直接載入詳細頁，徹底根除了 Stale Element 錯誤與點擊遮擋問題。
* **欄位清洗 (Field Cleaning) **：
	* **發表狀態**：擷取 `//tr[contains(@class, "status")]` 節點下的 `prefix` 文字，並透過 `.split("-")[0].strip()` 自動裁切掉後方多餘的年份。
	* **地點**：利用 `try-except` 補獲 `NoSuchElementException`，若該篇論文網頁未提供「國家/地區」欄位，系統將自動填入 `'None'` 字串，確保 CSV 資料列的完整與對齊。



## 注意事項與未來優化建議 (Notes & TODOs)

* **視窗不可干擾**：
程式開頭呼叫了 `driver.maximize_window()`。在執行期間，**請勿手動關閉、干擾瀏覽器視窗**。
若視窗寬度過窄，網站會觸發 RWD 響應式排版，導致頂部的 `main-search` 搜尋框被隱藏，進而引發 `ElementNotInteractableException`（元素無法互動）的錯誤。
* **網頁渲染超時**：
若遇到成大伺服器連線波動，30 秒顯式等待仍拋出 `TimeoutException` 導致教授被跳過，可適度將 `WebDriverWait(driver, 30)` 的數值調高。
* **年份參數化**：
目前年份「2023」為 hard-code 寫死在程式碼中，若日後需查詢其他年份，建議將目標年份抽離為函式的參數，增加程式的彈性與重用性。
* **防爬限制 (Rate Limiting)**：
若名單過長，頻繁的 request 可能會觸發伺服器的防爬蟲機制，建議在迴圈之間加上隨機的延遲時間。
