# NCKU Research Output Crawler (成大研究成果爬蟲)

## 📖 專案簡介

這是一個基於 Python 與 Selenium 實作的網頁自動化爬蟲專案。主要用途為自動擷取**國立成功大學 (NCKU) 學術研發成果網**上特定教授的「2023年度會議論文 (Conference contributions)」資訊。

透過批次讀取教授名單，系統會自動化開啟瀏覽器、搜尋教授、進入其研究成果頁面，並精準過濾出 2023 年度的會議論文，最後將每篇論文的詳細資訊結構化並匯出為 CSV 檔案，以利後續的學術表現統計與數據分析。

## ✨ 主要功能

* **自動化搜尋與導航**：動態尋找全域與區域搜尋框，自動搜尋教授名稱並跳轉至對應的「會議論文」列表頁。
* **特定年份過濾**：自動解析 DOM 結構中的年份標籤，精確定位並僅篩選出 **2023** 年度發表的論文（自動跳過更早或更晚的文獻）。
* **深層資訊擷取**：深入單一論文的詳細頁面，擷取以下核心資料：
* 作者列表 (Authors)
* 論文名稱 (Paper Title)
* 會議名稱 (Conference Name)
* 會議地點 (Location / Country)


* **結構化資料匯出**：即時將爬取結果（包含查詢的指導教授姓名）寫入 CSV 檔案。

## 🛠️ 環境與依賴套件 (Prerequisites)

在執行本專案前，請確保您的環境滿足以下條件：

1. **Python 3.7+**
2. **Selenium** 網頁自動化套件：
```bash
pip install selenium

```


3. **Chrome 瀏覽器與 ChromeDriver**：
* 程式預設使用 `webdriver.Chrome()`。
* 請確保已安裝與您本機 Google Chrome 瀏覽器版本相符的 ChromeDriver，並將其加入系統環境變數 (PATH) 中。



## 🚀 使用方法 (Usage)

1. **準備輸入檔案**：
在專案根目錄下準備一份名為 `professor_2.txt` 的純文字檔，將需要查詢的教授姓名逐行寫入：
```text
謝孫源
(其他教授姓名...)

```


2. **執行腳本**：
在終端機 (Terminal) 中執行以下指令開始爬取：
```bash
python web_crawler.py

```


*(執行期間 Chrome 瀏覽器會自動開啟並進行網頁操作，請勿手動關閉或干擾瀏覽器視窗)*
3. **取得輸出結果**：
程式執行完畢後，會自動關閉瀏覽器，並在同目錄下生成 `output_2.csv`，資料格式如下：
| 教師 | 作者 | 論文名稱 | 會議名稱 | 地點 |
| --- | --- | --- | --- | --- |
| 謝孫源 | 作者A, 作者B... | 論文的完整標題 | 發表會議全名 | 會議舉辦國家/地區 |



## 🏗️ 程式碼架構 (Architecture)

* **`read_txt(path)`**: 輔助函式。負責讀取 TXT 檔案並過濾換行符號，回傳乾淨的教授名稱 List。
* **`web_crawler(professor_list, save_path)`**: 爬蟲核心邏輯。
* 採用 `csv.writer` 確保資料可穩定寫入。
* 結合 XPath 與 CSS Selector 進行精準的網頁元素定位。
* 實作條件判斷 (`conference_info[0] == '2023'`)，動態控制 Crawler 應進入哪些 `.list-result-item` 節點。



## ⚠️ 注意事項與未來優化建議 (Notes & TODOs)

1. **顯式等待 (Explicit Waits) 升級**：
目前程式碼依賴 `time.sleep()` 進行強制等待以配合網頁渲染。在不同的網路速度下可能會造成執行過慢或抓取失敗（`NoSuchElementException`）。**建議未來**可導入 `WebDriverWait` 與 `expected_conditions` 來取代 `time.sleep()`，提升程式穩定度與執行效率。
2. **年份參數化**：
目前年份「2023」為 hard-code 寫死在程式碼中，若日後需查詢其他年份，建議將目標年份抽離為函式的參數，增加程式的彈性與重用性。
3. **異常處理 (Exception Handling)**：
目前若遇到無法預期的網頁錯誤（例如某位教授未建檔、或沒有任何研究成果），程式可能發生中斷。建議在 `driver.find_element` 外層加入 `try...except` 區塊，以確保爬蟲能在記錄錯誤後繼續執行下一位教授的搜尋。
4. **防爬限制 (Rate Limiting)**：
若名單過長，頻繁的 request 可能會觸發成大伺服器的防爬蟲機制，建議在迴圈之間加上隨機的延遲時間。
