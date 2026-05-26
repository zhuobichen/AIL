import requests
import os
import urllib.parse

def download_longzu():
    print("开始从 GitHub 原地址下载《龙族》系列纯文本资源...")
    base_url = "https://raw.githubusercontent.com/ChengzhuLi/Novel/master/"
    
    files_to_download = [
        ("龙族1+2+外传+前传.txt", "龙族1_2.txt"),
        ("龙族Ⅲ黑月之潮（1）.txt", "龙族3_1.txt"),
        ("龙族Ⅲ黑月之潮（2）.txt", "龙族3_2.txt"),
        ("龙族Ⅲ黑月之潮（3）.txt", "龙族3_3.txt"),
    ]
    
    combined_text = ""
    
    # 尝试常见的本地代理端口，如果用户开了科学上网，通常在这个端口
    proxies = {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890",
    }
    
    for url_name, save_name in files_to_download:
        url = base_url + urllib.parse.quote(url_name)
        print(f"\n正在下载: {save_name} ...")
        try:
            # 先尝试不带显式代理（依赖系统全局代理/TUN模式）
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            print(f"  -> 直连成功！")
        except Exception as e1:
            print(f"  -> 直连失败或超时，尝试使用常见本地代理 (127.0.0.1:7890)...")
            try:
                response = requests.get(url, timeout=15, proxies=proxies)
                response.raise_for_status()
                print(f"  -> 代理连接成功！")
            except Exception as e2:
                print(f"  -> 代理下载也失败了: {e2}")
                continue
                
        text = response.text
        print(f"  -> {save_name} 下载完成，长度: {len(text)} 字符")
        combined_text += f"\n\n\n=== {save_name} ===\n\n\n" + text
            
    if combined_text:
        out_file = "longzu_full.txt"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(combined_text)
        print(f"\n✅ 全部下载完成！已合并保存至 {out_file}，总长度: {len(combined_text)} 字符。")
    else:
        print("\n❌ 未下载到任何内容。请检查科学上网节点是否正常工作，或者代理端口是否为 7890。")

if __name__ == "__main__":
    download_longzu()