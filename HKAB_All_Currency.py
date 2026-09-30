#@title Python爬取HKAB Currency Rate (with GUI)
# Author: Victor Suen
# Version: 2.0

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import threading
import subprocess

class HKABRateScraper:
    def __init__(self):
        self.base_url = "https://www.hkab.org.hk/tc/rates/exchange-rates"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.hkab.org.hk/tc/rates/exchange-rates",
            "Origin": "https://www.hkab.org.hk",
            "Connection": "keep-alive",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.max_redirects = 5

    def get_currency_rates(self, date_obj, currency_code):
        """根據日期和幣種代碼獲取對應匯率資料"""
        try:
            date_str = date_obj.strftime("%Y-%m-%d")
            url = f"https://www.hkab.org.hk/api/member/public/getExrate/{date_str}"
            print(f"正在請求API: {url}")
            response = self.session.get(url, timeout=10)
            print(f"響應狀態碼: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            # 假日或無當日牌價時，API 會把上一個有牌價的日子整份回傳。
            # 必須對上 RateDate，否則 7 月 1 日這類空日會被填成前一日匯率。
            rate_date = str(data.get("RateDate") or "")[:10]
            if data.get("holiday") or rate_date != date_str:
                return None
            sell = data.get(f"{currency_code}Selling", "")
            buy_tt = data.get(f"{currency_code}BuyingTT", "")
            buy_od = data.get(f"{currency_code}BuyingOD", "")
            if not (sell or buy_tt or buy_od):
                return None
            return {
                "日期": date_str,
                "賣出價": sell,
                "電匯買入價": buy_tt,
                "匯票買入價": buy_od
            }
        except Exception as e:
            print(f"處理數據時出錯 ({date_obj.strftime('%Y-%m-%d')}): {str(e)}")
            return None

    def collect_historical_rates(self, start_date, end_date):
        """收集指定日期範圍內的CNH匯率（僅抓取當天最新）"""
        all_rates = []
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        processed_days = 0
        while current_date <= end_date:
            processed_days += 1
            progress = (processed_days / total_days) * 100
            print(f"\n進度: {progress:.1f}% - 正在獲取 {current_date.strftime('%Y-%m-%d')} 的數據...")
            # 只抓取當天最新（網站只提供最新一日）
            if current_date == datetime.today().date():
                rates_data = self.get_currency_rates(current_date, "CNH")
                if rates_data:
                    all_rates.append(rates_data)
                    print(f"已成功保存 {rates_data['日期']} 的數據")
                else:
                    print(f"{current_date.strftime('%Y-%m-%d')} 無資料")
            else:
                print(f"{current_date.strftime('%Y-%m-%d')} 只能抓取最新一日資料，跳過")
            time.sleep(0.5)
            current_date += timedelta(days=1)
        return all_rates

    def save_to_excel(self, data, filename):
        """將數據保存到Excel文件"""
        if not data:
            print("沒有數據可保存")
            return False
        try:
            root = tk.Tk()
            root.withdraw()
            save_path = filedialog.askdirectory(title="選擇保存位置")
            if not save_path:
                print("未選擇保存位置，將保存在當前目錄")
                save_path = os.getcwd()
            full_path = os.path.join(save_path, filename)
            df = pd.DataFrame(data)
            df.set_index('日期', inplace=True)
            df.to_excel(full_path)
            print(f"\n數據已成功保存到 {full_path}")
            print(f"共保存了 {len(data)} 天的數據")
            return True
        except Exception as e:
            print(f"保存數據時出錯: {str(e)}")
            return False

class HKABRateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HKAB Currency Rate 下載器 v2.0")
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        
        # 幣種列表
        self.currency_list = [
            "AUD", "BND", "CAD", "CHF", "DKK", "EUR", "INR", "JPY", "MYR", "NOK", "NTD", "NZD", "PHP", "PKR", "CNY", "CNH", "SEK", "SGD", "THB", "USD", "WON", "ZAR", "GBP"
        ]
        self.currency_var = tk.StringVar(value="CNH")
        
        # 設置變量
        self.save_path_var = tk.StringVar(value="C:/Users/victor.suen/Desktop")  # 更改默認路徑
        self.remember_path_var = tk.BooleanVar(value=True)
        self.is_downloading = False
        
        self.create_gui()
        
    def create_gui(self):
        # 標題標籤
        title_label = ttk.Label(self.root, text="HKAB Currency Rate 下載器", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 作者信息
        author_label = ttk.Label(self.root, text="作者: Victor Suen | 版本: 2.0", font=("Arial", 10))
        author_label.pack()
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 日期選擇框架
        date_frame = ttk.LabelFrame(main_frame, text="日期範圍選擇")
        date_frame.pack(fill="x", padx=5, pady=5)
        
        # 開始日期
        ttk.Label(date_frame, text="開始日期:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2)
        self.start_date.grid(row=0, column=1, padx=5, pady=5)
        
        # 結束日期
        ttk.Label(date_frame, text="結束日期:").grid(row=0, column=2, padx=5, pady=5)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.end_date.grid(row=0, column=3, padx=5, pady=5)
        
        # 幣種選擇
        currency_frame = ttk.LabelFrame(main_frame, text="幣種選擇")
        currency_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(currency_frame, text="選擇幣種:").grid(row=0, column=0, padx=5, pady=5)
        currency_combo = ttk.Combobox(currency_frame, textvariable=self.currency_var, values=self.currency_list, state="readonly", width=10)
        currency_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # 保存路徑框架
        path_frame = ttk.LabelFrame(main_frame, text="保存設置")
        path_frame.pack(fill="x", padx=5, pady=5)
        
        # 保存路徑
        ttk.Label(path_frame, text="保存路徑:").grid(row=0, column=0, padx=5, pady=5)
        path_entry = ttk.Entry(path_frame, textvariable=self.save_path_var, width=50)
        path_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 選擇路徑按鈕
        browse_btn = ttk.Button(path_frame, text="瀏覽", command=self.browse_path)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 記住路徑選項
        remember_path_check = ttk.Checkbutton(path_frame, text="記住此路徑",
                                            variable=self.remember_path_var)
        remember_path_check.grid(row=1, column=1, sticky="w", padx=5)
        
        # 進度框架
        progress_frame = ttk.LabelFrame(main_frame, text="下載進度")
        progress_frame.pack(fill="x", padx=5, pady=5)
        
        # 進度條
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                          maximum=100, mode='determinate')
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        
        # 進度標籤
        self.progress_label = ttk.Label(progress_frame, text="準備就緒")
        self.progress_label.pack(pady=5)
        
        # 按鈕框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", padx=5, pady=10)
        
        # 開始下載按鈕
        self.download_btn = ttk.Button(button_frame, text="開始下載",
                                     command=self.start_download)
        self.download_btn.pack(side="left", padx=5)
        
        # 打開文件夾按鈕
        self.open_folder_btn = ttk.Button(button_frame, text="打開下載文件夾",
                                        command=self.open_folder)
        self.open_folder_btn.pack(side="right", padx=5)
        
    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path_var.set(path)
            
    def open_folder(self):
        path = self.save_path_var.get()
        if os.path.exists(path):
            if os.name == 'nt':  # Windows
                os.startfile(path)
            else:  # macOS 和 Linux
                subprocess.run(['open' if os.name == 'darwin' else 'xdg-open', path])
        else:
            messagebox.showerror("錯誤", "文件夾不存在！")
            
    def update_progress(self, value, text):
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.root.update_idletasks()
        
    def start_download(self):
        if self.is_downloading:
            return
            
        # 獲取日期
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        
        # 驗證日期
        if start_date > end_date:
            messagebox.showerror("錯誤", "開始日期不能晚於結束日期！")
            return
            
        # 驗證保存路徑
        save_path = self.save_path_var.get()
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except Exception as e:
                messagebox.showerror("錯誤", f"創建保存路徑失敗：{str(e)}")
                return
        
        # 禁用按鈕
        self.download_btn.config(state="disabled")
        self.is_downloading = True
        
        # 在新線程中執行下載
        thread = threading.Thread(target=self.download_data,
                               args=(start_date, end_date, save_path))
        thread.daemon = True
        thread.start()
        
    def download_data(self, start_date, end_date, save_path):
        try:
            scraper = HKABRateScraper()
            total_days = (end_date - start_date).days + 1
            processed_days = 0
            all_rates = []
            current_date = start_date
            currency_code = self.currency_var.get()
            while current_date <= end_date:
                processed_days += 1
                progress = (processed_days / total_days) * 100
                self.update_progress(progress, f"正在下載 {current_date.strftime('%Y-%m-%d')} {currency_code} 的數據... ({processed_days}/{total_days})")
                rates_data = scraper.get_currency_rates(current_date, currency_code)
                if rates_data:
                    all_rates.append(rates_data)
                else:
                    self.update_progress(progress, f"{current_date.strftime('%Y-%m-%d')} 沒有抓到{currency_code}數據")
                current_date += timedelta(days=1)
                time.sleep(0.5)
            if all_rates:
                filename = f"HKAB_{currency_code}_HKD_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.xlsx"
                full_path = os.path.join(save_path, filename)
                self.update_progress(95, "正在保存數據...")
                df = pd.DataFrame(all_rates)
                df.set_index('日期', inplace=True)
                df.to_excel(full_path)
                self.update_progress(100, f"完成！已保存 {len(all_rates)} 天的數據")
                messagebox.showinfo("完成", f"數據已成功保存到：\n{full_path}")
            else:
                self.update_progress(0, "未能獲取任何數據。請確認所選日期範圍內有資料。")
                messagebox.showerror("錯誤", "未能獲取任何數據。請確認所選日期範圍內有資料。")
        except Exception as e:
            self.update_progress(0, f"錯誤：{str(e)}")
            messagebox.showerror("錯誤", str(e))
        finally:
            self.download_btn.config(state="normal")
            self.is_downloading = False

def main():
    root = tk.Tk()
    app = HKABRateGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
