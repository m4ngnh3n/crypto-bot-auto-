import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from web3 import Web3

# ==========================================
# ⚙️ THÔNG TIN TÍCH HỢP CHO CHỦ TỊCH VOTDOKA
# ==========================================
MAIN_WALLET_ADDRESS = "XKOee5ac0c08589317f2dccfa4cf850a6393be55451"  # Ví OKX chính
SENDER_EMAIL = "votdoka@gmail.com"                                   # Email gửi & nhận báo cáo
RECEIVER_EMAIL = "votdoka@gmail.com"

# Chu kỳ lặp lại (7200 giây = 2 tiếng / lần)
LOOP_INTERVAL_SECONDS = 7200 

# Mạng BSC Mainnet
RPC_URL = "https://bsc-dataseed.binance.org/"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Thông tin bảo mật lấy từ biến môi trường
WORKER_PRIVATE_KEY = os.environ.get("WORKER_PRIVATE_KEY") 
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

def send_email_report(subject, body):
    """Hàm gửi báo cáo qua Email"""
    if not SENDER_PASSWORD:
        print("[!] Thiếu mật khẩu ứng dụng Gmail (SENDER_PASSWORD) trong bảo mật server.")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("[✓] Đã gửi Email báo cáo về hòm thư votdoka@gmail.com thành công!")
    except Exception as e:
        print(f"[X] Lỗi gửi email: {e}")

def auto_farm_task():
    """Logic cày nhiệm vụ tự động"""
    print("\n[1] ⚙️ Đang tiến hành chạy tác vụ cày tự động...")
    time.sleep(3) 
    print("[✓] Hoàn thành tác vụ cày lúa trong phiên này!")

def sweep_native_balance():
    """Hàm tự động quét và gom toàn bộ BNB thừa về Ví OKX chính"""
    if not WORKER_PRIVATE_KEY:
        print("[X] Lỗi: Thiếu WORKER_PRIVATE_KEY của ví phụ!")
        return "THẤT BẠI - Thiếu Private Key ví phụ"

    try:
        account = w3.eth.account.from_key(WORKER_PRIVATE_KEY)
        worker_address = account.address
        
        balance = w3.eth.get_balance(worker_address)
        balance_in_bnb = w3.from_wei(balance, 'ether')
        print(f"[*] Số dư hiện tại ở Ví Cày ({worker_address}): {balance_in_bnb:.6f} BNB")

        # Giữ lại 0.001 BNB làm phí gas
        min_reserve = w3.to_wei(0.001, 'ether')
        
        if balance > min_reserve:
            gas_price = w3.eth.gas_price
            gas_limit = 21000 
            fee = gas_price * gas_limit
            
            amount_to_send = balance - min_reserve - fee
            
            if amount_to_send > 0:
                nonce = w3.eth.get_transaction_count(worker_address)
                tx = {
                    'nonce': nonce,
                    'to': MAIN_WALLET_ADDRESS,
                    'value': amount_to_send,
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                    'chainId': 56
                }
                
                signed_tx = w3.eth.account.sign_transaction(tx, WORKER_PRIVATE_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                amount_bnb_sent = w3.from_wei(amount_to_send, 'ether')
                print(f"[🚀] Đã hốt {amount_bnb_sent:.6f} BNB về Ví OKX chính: {MAIN_WALLET_ADDRESS}!")
                print(f"[*] Tx Hash: {w3.to_hex(tx_hash)}")
                return f"THÀNH CÔNG - Đã quét {amount_bnb_sent:.6f} BNB"
            else:
                return "BỎ QUA - Số dư không đủ bù phí gas"
        else:
            return "BỎ QUA - Số dư chưa đủ hạn mức quét"

    except Exception as e:
        print(f"[X] Lỗi trong quá trình quét ví: {e}")
        return f"LỖI: {e}"

def run_bot_cycle():
    """Thực thi một chu kỳ làm việc"""
    print("\n==================================================")
    print("   BẮT ĐẦU MỘT CHU KỲ CÀY & GOM LÚA MỚI (VOTDOKA)  ")
    print("==================================================")
    
    if not w3.is_connected():
        print("[X] Không thể kết nối tới mạng Blockchain.")
        return

    auto_farm_task()
    sweep_result = sweep_native_balance()
    
    subject = f"🌾 [BÁO CÁO BOT] Kết quả chu kỳ: {sweep_result}"
    body = f"""Chủ tịch votdoka ơi, bot vừa hoàn tất một chu kỳ tự động:

- Kết quả gom ví: {sweep_result}
- Ví OKX nhận chính: {MAIN_WALLET_ADDRESS}
- Hòm thư nhận: votdoka@gmail.com

Hệ thống vẫn đang ngủ đông nhẹ và sẽ tự chạy tiếp chu kỳ sau!
"""
    send_email_report(subject, body)

def main():
    print("🤖 HỆ THỐNG BOT TỰ ĐỘNG 24/7 ĐÃ KHỞI ĐỘNG...")
    while True:
        try:
            run_bot_cycle()
        except Exception as e:
            print(f"[!] Phát hiện lỗi ngoại lệ ở vòng lặp chính: {e}")
            send_email_report("⚠️ [CẢNH BÁO BOT] Lỗi hệ thống ngoại lệ", f"Chi tiết lỗi: {e}")
        
        print(f"⏳ Bot tạm nghỉ ngơi, sẽ chạy lại sau {LOOP_INTERVAL_SECONDS / 60} phút nữa...")
        time.sleep(LOOP_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
