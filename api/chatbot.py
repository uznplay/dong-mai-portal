import json
import requests
from ddgs import DDGS
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import os
import hashlib
import base64
import time
import random
from datetime import datetime, timedelta, timezone

# Load .env explicitly from current directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)
else:
    # Try current working directory
    from dotenv import load_dotenv
    load_dotenv()

ZAI_KEYS_STR = os.getenv("ZAI_API_KEYS", "")
ZAI_KEYS = [k.strip() for k in ZAI_KEYS_STR.split(",") if k.strip()]
if not ZAI_KEYS:
    fallback_zai = os.getenv("ZAI_API_KEY")
    if fallback_zai:
        ZAI_KEYS = [fallback_zai]
READER_URL = "https://api.z.ai/api/paas/v4/reader"
LLM_URL = "https://api.z.ai/api/paas/v4/chat/completions"

ALLOWED_DOMAINS = ["dichvucong.gov.vn", "luatvietnam.vn", "luat247.vn", "vbpl.vn", "moj.gov.vn", "moha.gov.vn", "gov.vn"]

# Danh sách viết tắt phổ biến cần mở rộng để search chính xác hơn
ABBREVIATIONS = {
    "cccd": "căn cước công dân",
    "bhyt": "bảo hiểm y tế",
    "bhxh": "bảo hiểm xã hội",
    "vneid": "định danh điện tử mức 2",
    "dkkh": "đăng ký kết hôn", 
    "kcb": "khám chữa bệnh",
    "ubnd": "ủy ban nhân dân",
    "hđnd": "hội đồng nhân dân",
    "xd": "xây dựng",
    "xe": "đăng ký xe", # "mua xe" -> "đăng ký xe"
    "sổ đỏ": "giấy chứng nhận quyền sử dụng đất"
}

def expand_query(query):
    query_lower = query.lower()
    # Mở rộng các từ đơn lẻ hoặc cụm từ
    for short, long in ABBREVIATIONS.items():
        if short in query_lower.split():
            query_lower = query_lower.replace(short, long)
    return query_lower

def get_search_results(query):
    # 1. Mở rộng từ viết tắt
    expanded_query = expand_query(query)
    
    candidates = []
    
    # 2. Thử search nghiêm ngặt (có site:...)
    trusted_query = f"{expanded_query} (site:gov.vn OR site:luatvietnam.vn OR site:luat247.vn OR site:vbpl.vn)"
    
    
    with DDGS() as ddgs:
        try:
            results = list(ddgs.text(trusted_query, region='vi-vn', max_results=6))
        except Exception as e:
            results = []
            
        
        is_fallback = False
        # Nếu không có kết quả, thử search rộng
        if not results:
            is_fallback = True
            try:
                results = list(ddgs.text(expanded_query, region='vi-vn', max_results=6))
            except Exception as e:
                results = []

        for r in results:
            url = r.get('href', '').lower()
            
            # Bỏ qua các trang không nội dung
            if "dangky.dichvucong.gov.vn" in url or "dvc-thanh-toan-truc-tuyen" in url:
                continue
            
            # Layer 1: Các domain tin cậy tuyệt đối
            if any(domain in url for domain in ALLOWED_DOMAINS):
                candidates.append(url)
            # Layer 2: Nếu là fallback broad search, cho phép thêm các site .gov.vn bất kỳ
            elif is_fallback and ".gov.vn" in url:
                candidates.append(url)
        
        # Sắp xếp ưu tiên: Luật VN / Luat247 / VBPL / Dịch vụ công lên đầu
        filtered = sorted(candidates, key=lambda x: 0 if any(d in x for d in ["luatvietnam.vn", "luat247.vn", "vbpl.vn", "dichvucong.gov.vn"]) else 1)[:1]
        
        if not filtered:
            pass
        else:
            pass
        return filtered

def read_web_page_local(url):
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style", "header", "footer", "nav", "aside"]):
                script.decompose()
                
            text = soup.get_text(separator='\n')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
    except Exception as e:
        print(f"Local read error for {url}: {e}")
    return ""

def read_web_page(url):
    # Sử dụng Google Apps Script để đọc nội dung trang web
    # API: https://script.google.com/macros/s/AKfycbzyBA7e4PdLn8fn_wDOVU1LvZtpzOVNlntnHJqEOgqOfDvn-7pzPi7yaL5_pIstS0BG/exec
    try:
        google_script_url = "https://script.google.com/macros/s/AKfycbzyBA7e4PdLn8fn_wDOVU1LvZtpzOVNlntnHJqEOgqOfDvn-7pzPi7yaL5_pIstS0BG/exec"
        params = {"url": url}
        response = requests.get(google_script_url, params=params, timeout=20, allow_redirects=True)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("status") == "success" and data.get("content"):
                    content_len = len(data.get("content", ""))
                    return data.get("content", "")
                else:
                    pass
            except:
                pass
        else:
            pass
    except Exception as e:
        print(f"ERROR reading {url} with Google Script: {e}")
    
    # Fallback: Dùng "cây nhà lá vườn" (Local Fallback)
    return read_web_page_local(url)

from supabase import create_client, Client
import requests

# Cấu hình Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- GEOBLOCKING CONFIG ---
ALLOWED_COUNTRIES = ["VN"]  # Chỉ cho phép Việt Nam

def get_country_from_ip(ip):
    """Lấy mã quốc gia từ IP sử dụng ip-api.com (miễn phí)"""
    # Bỏ qua localhost và private IPs
    if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
        return "VN"  # Assume local is allowed
    
    try:
        # Sử dụng ip-api.com (free: 45 requests/minute)
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return data.get("countryCode", "")
    except Exception as e:
        print(f"GeoIP Error: {e}")
    
    return None  # Unknown

def check_geo_allowed(ip):
    """Kiểm tra IP có thuộc quốc gia được cho phép không"""
    country = get_country_from_ip(ip)
    if country is None:
        # Nếu không xác định được, cho phép (tránh chặn nhầm)
        print(f"WARNING: Could not determine country for IP {ip}, allowing...")
        return True
    
    allowed = country in ALLOWED_COUNTRIES
    if not allowed:
        pass
    else:
        pass
    
    return allowed

OR_KEYS_STR = os.getenv("OPENROUTER_API_KEYS", "")
OPENROUTER_KEYS = [k.strip() for k in OR_KEYS_STR.split(",") if k.strip()]
if not OPENROUTER_KEYS:
    # Fallback to single key if comma-separated not found
    fallback_key = os.getenv("OPENROUTER_API_KEY")
    if fallback_key:
        OPENROUTER_KEYS = [fallback_key]

class ModelRouter:
    def __init__(self):
        self.providers = {
            "zai": {
                "url": LLM_URL,
                "keys": ZAI_KEYS
            },
            "openrouter": {
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "keys": OPENROUTER_KEYS
            }
        }
        # Keep track of current key index per provider
        self.key_indices = {p: 0 for p in self.providers}
        # Mô phỏng theo yêu cầu: ZAI chỉ dùng cho Reader, OpenRouter dùng cho Chat
        # TUY NHIÊN: Thêm Z.AI Direct làm back-up cuối cùng nếu OpenRouter bị nghẽn
        self.models = [
            # Priority 1: Requested Free models (OpenRouter)
            ("liquid/lfm-2.5-1.2b-instruct:free", "openrouter"),
            ("qwen/qwen3-next-80b-a3b-instruct:free", "openrouter"),
            ("z-ai/glm-4.5-air:free", "openrouter"),
            ("google/gemini-2.0-flash-exp:free", "openrouter"), # Good reliable free tier
            
            # Priority 2: Reliable Backup models (7B+ OpenRouter)
            # Hệ thống sẽ tự động "treo giò" (ban) 20 phút nếu model bị lỗi
            ("meta-llama/llama-3.3-70b-instruct:free", "openrouter"),
            ("qwen/qwen-2.5-vl-7b-instruct:free", "openrouter"),
            ("allenai/molmo-2-8b:free", "openrouter"),
            ("openai/gpt-oss-20b:free", "openrouter"),
            ("moonshotai/kimi-k2:free", "openrouter"),
            ("arcee-ai/trinity-large-preview:free", "openrouter"),
            
            # Priority 3: Z.AI Direct Fallback (Emergency & Anti-congestion)
            # Tier A: Free / Ultra-Low Cost "Reader" Class (Flash Models)
            ("glm-4.7-flash", "zai"),
            ("glm-4.6v-flash", "zai"),
            ("glm-4.5-flash", "zai"),
            
            # Tier B: Efficient / Low Cost (Air & FlashX Models)
            ("glm-4.7-flashx", "zai"),
            ("glm-4.6v-flashx", "zai"),
            ("glm-4.5-air", "zai"),
            ("glm-4.5-airx", "zai"),
            ("glm-4.5-flashx", "zai"),
            
            # Tier C: High Performance / Standard Cost (Flagship Models)
            ("glm-4.7", "zai"),
            ("glm-4.6", "zai"), 
            ("glm-4.6v", "zai"),
            ("glm-4.5", "zai"),
            ("glm-4.5v", "zai"),
            ("glm-4.5-x", "zai")
        ]
        self.max_queue_retries = 3
        self.base_wait_time = 2

    def get_blacklisted_models(self):
        """Lấy danh sách các model đang bị 'treo giò' trong 20 phút qua"""
        try:
            limit_time = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
            response = supabase.table("model_health") \
                .select("model_id") \
                .gt("last_failure_at", limit_time) \
                .execute()
            if response.data:
                return [item["model_id"] for item in response.data]
        except Exception as e:
            print(f"Health Check Error: {e}")
        return []

    def report_failure(self, model_id):
        """Báo cáo model bị lỗi để tạm ngưng sử dụng"""
        try:
            print(f"REPORTING FAILURE: {model_id} -> Banned for 20 mins")
            supabase.table("model_health").upsert({
                "model_id": model_id,
                "last_failure_at": datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception as e:
            print(f"Report Failure Error: {e}")

    def call_api(self, model_info, messages):
        model_id, provider = model_info
        config = self.providers[provider]
        keys = config['keys']
        
        # Rotate to the next key index BEFORE starting, to ensure alternating (round-robin) usage
        num_keys = len(keys)
        self.key_indices[provider] = (self.key_indices[provider] + 1) % num_keys
        start_idx = self.key_indices[provider]
        
        for k_offset in range(num_keys):
            curr_idx = (start_idx + k_offset) % num_keys
            api_key = keys[curr_idx]
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            if provider == "openrouter":
                headers["HTTP-Referer"] = "http://localhost:8081"
                headers["X-Title"] = "Dong Mai Portal"
                
            data = {
                "model": model_id,
                "messages": messages,
                "max_tokens": 2048, # Limit output to prevent errors with models like Qwen/Llama
                "temperature": 0.5,
                "top_p": 0.9,
                "repetition_penalty": 1.1,
            }
            
            try:
                
                # Dynamic Timeout: Use 30s or remaining time, whichever is smaller
                # (Leave 2s buffer for cleanup)
                current_timeout = 30
                if 'remaining_time' in config and config['remaining_time'] > 0:
                     current_timeout = max(5, min(30, int(config['remaining_time']) - 2))

                response = requests.post(config['url'], headers=headers, json=data, timeout=current_timeout)
                
                if response.status_code == 200:
                    res_json = response.json()
                    if "choices" in res_json and len(res_json["choices"]) > 0:
                        # Save successful key index
                        self.key_indices[provider] = curr_idx
                        return res_json["choices"][0]["message"]["content"]
                    return None
                
                # If key is bad/expired/exhausted (401, 402, 403, 429) -> Try next key
                if response.status_code in [401, 402, 403, 429]:
                    if response.status_code == 429:
                        time.sleep(1) # Wait 1s before switching key to avoid spamming
                    continue
                
                # If 503 or other server errors, it might be the model itself or the provider endpoint
                if response.status_code in [503, 502, 504]:
                    return None

                return None
                
            except Exception as e:
                print(f"EXCEPTION calling {model_id} with key {curr_idx}: {e}")
                # For critical errors (Timeout/Connection), BAN immediately.
                # Don't wait for Vercel to kill the process.
                if "timeout" in str(e).lower() or "connection" in str(e).lower() or "refused" in str(e).lower():
                     self.report_failure(model_id)
                continue
                
        return None

    def execute(self, messages):
        # Tổng thời gian tối đa cho phép xử lý AI (để chừa đường lui cho Vercel 60s)
        start_time = time.time()
        MAX_TOTAL_DURATION = 40 
        
        # 1. Lấy danh sách đen (Blacklist)
        blacklisted = self.get_blacklisted_models()
        if blacklisted:
            pass

        # 2. Lọc & Xáo trộn danh sách model
        # Chỉ giữ lại model KHÔNG nằm trong blacklist
        viable_models = [m for m in self.models if m[0] not in blacklisted]
        
        # Nếu blacklist hết sạch thì đành phải thử đại (Fallback cực đoan)
        if not viable_models:
            print("WARNING: All models are blacklisted! Forcing retry on all.")
            viable_models = self.models.copy()

        # Khôi phục random shuffle theo yêu cầu User
        random.shuffle(viable_models)
        
        for attempt in range(self.max_queue_retries + 1):
            if time.time() - start_time > MAX_TOTAL_DURATION:
                break
                
            for model_info in viable_models:
                # Calculate remaining time for this specific attempt
                remaining = MAX_TOTAL_DURATION - (time.time() - start_time)
                if remaining <= 5: # Not enough time for even a fast call
                    break
                    
                # Pass remaining time to call_api via provider config (volatile but effective)
                self.providers[model_info[1]]['remaining_time'] = remaining
                
                result = self.call_api(model_info, messages)
                if result:
                    return result
                else:
                    # report_failure already called inside call_api for critical errors, 
                    # but call it here too for Logic/Empty results.
                    self.report_failure(model_info[0])
            
            if attempt < self.max_queue_retries:
                if time.time() - start_time < MAX_TOTAL_DURATION:
                    wait_time = self.base_wait_time * (attempt + 1) + random.uniform(0, 1)
                    print(f"All viable models busy. Queueing for {wait_time:.2f}s...")
                    time.sleep(wait_time)
        
        return "Hiện tại hệ thống AI đang quá tải và không phản hồi kịp (Timeout). Vui lòng thử lại sau ít phút."
        
# Khởi tạo Router toàn cục
ai_router = ModelRouter()

def get_session_history(session_id):
    try:
        # Chỉ lấy tin nhắn trong vòng 10 phút gần nhất.
        # Nếu session cũ quá 10p -> Coi như session mới -> history = [] -> Sẽ trigger search lại.
        limit_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        
        response = supabase.table("chat_history") \
            .select("*") \
            .eq("session_id", session_id) \
            .gt("created_at", limit_time) \
            .order("created_at", desc=True) \
            .limit(6) \
            .execute()
            
        # Đảo ngược lại để đúng thứ tự thời gian (Cũ -> Mới)
        data = response.data[::-1] if response.data else []
        return [{"role": item["role"], "content": item["content"]} for item in data]
    except Exception as e:
        print(f"Supabase Read Error: {e}")
        return []

def save_message(session_id, role, content):
    try:
        # 1. Insert tin nhắn mới (Database Trigger sẽ tự động xóa tin cũ > 10p)
        supabase.table("chat_history").insert({
            "session_id": session_id,
            "role": role,
            "content": content
        }).execute()
        
    except Exception as e:
        print(f"Supabase Write/Cleanup Error: {e}")

def normalize_text(text):
    """Chuẩn hóa văn bản: viết thường, loại bỏ khoảng trắng thừa đầu/cuối và giữa các từ"""
    if not text:
        return ""
    # Loại bỏ khoảng trắng thừa giữa các từ bằng split() và join()
    return " ".join(text.lower().split())

def get_cached_answer(question):
    """Tìm câu trả lời trong cache (chỉ dành cho câu hỏi đầu tiên)"""
    try:
        norm_q = normalize_text(question)
        response = supabase.table("qa_cache").select("answer_text").eq("question_text", norm_q).execute()
        if response.data:
            ans = response.data[0]["answer_text"]
            return ans.replace("Một cửa", "Hành chính công")
    except Exception as e:
        print(f"Cache Lookup Error: {e}")
    return None

def save_to_cache(question, answer):
    """Lưu câu trả lời vào cache"""
    try:
        norm_q = normalize_text(question)
        # Chỉ lưu nếu câu trả lời có nội dung và không phải tin báo lỗi hệ thống
        if answer and "xin lỗi" not in answer.lower() and "không tìm thấy" not in answer.lower() and "hệ thống AI đang quá tải" not in answer:
            # Dùng upsert để cập nhật câu trả lời mới nhất nếu trùng câu hỏi
            supabase.table("qa_cache").upsert({
                "question_text": norm_q,
                "answer_text": answer
            }).execute()
    except Exception as e:
        print(f"Cache Save Error: {e}")

def is_greeting_or_trivial(text):
    """Kiểm tra xem câu hỏi có phải là chào hỏi (trong danh sách) không"""
    if not text: return False # Empty text -> Not a greeting
    text = text.lower().strip()
    greetings = [
        "hi", "hello", "xin chào", "chào", "alo", "test", "ê", "ơi", "bạn ơi", "bạn là ai",
        "chào bạn", "chào ad", "hi ad", "chào admin", "hỏi tí", "cho hỏi", "mình hỏi chút", 
        "có ai không", "giúp với", "giúp mình", "hú", "hi shop"
    ]
    if text in greetings: return True
    # BỎ logic tự động coi tin ngắn là Trivial/Greeting để tránh lưu cache rác (như 'sdahjhpoqwi')
    return False

import math
from collections import Counter

def calculate_entropy(text):
    """Tính Shannon Entropy của chuỗi"""
    if not text: return 0
    entropy = 0
    total_len = len(text)
    counts = Counter(text)
    for count in counts.values():
        p = count / total_len
        entropy -= p * math.log2(p)
    return entropy

def is_gibberish(text):
    """
    Phát hiện tin nhắn rác/vô nghĩa dựa trên các thuật toán:
        pass
    1. Độ dài từ quá khổ
    2. Thiếu nguyên âm
    3. Độ hỗn loạn (Entropy)
    4. Keyboard Patterns
    5. Consecutive Consonants (Chuỗi phụ âm liên tiếp)
    """
    if not text: return False
    text_lower = text.lower().strip()
    
    # 1. Check độ dài từ (Long Word)
    words = text_lower.split()
    if any(len(w) > 25 for w in words):
        return True

    # 2. Check Nguyên âm (Vowel Check)
    vowels = set("aeiouyàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ")
    has_vowel = any(char in vowels for char in text_lower)
    # Tăng độ nhạy cho tin ngắn (VD: sdfg - 4 char, no vowel)
    if len(text_lower) >= 3 and not has_vowel:
        # User yêu cầu: Nếu gửi mỗi "cccd", "ubnd" một mình thì cũng chặn
        # Vì các từ này luôn phải đi kèm một ngữ cảnh/động từ
        words_list = text_lower.split()
        if len(words_list) == 1:
             return True
             
        # Nếu có từ khác đi kèm (hỏi cccd...) thì mới bypass
        if text_lower not in ["cccd", "bhxh", "bhyt", "vneid", "kcb", "ubnd", "hđnd", "dkkh"]:
            return True

    # 3. Check Entropy
    ent = calculate_entropy(text_lower)
    if len(text_lower) > 10:
        if ent < 1.0: # Quá lặp
             return True
        if ent > 6.0: # Quá loạn
             return True

    # 4. Check Keyboard Rows
    keyboard_patterns = ["asdf", "qwer", "zxcv", "jkl", "12345", "hjkl"]
    if any(pat in text_lower for pat in keyboard_patterns) and len(text_lower) > 10:
        return True

    # 5. Check Consecutive Consonants (Phụ âm liên tiếp)
    # VD: "hjhpoqw" -> h,j,h,p (4) -> q,w (2)
    # Nếu có > 4 phụ âm liên tiếp mà không phải chữ cái ghép (như 'ngh') -> Nghi vấn
    consonant_count = 0
    max_consonants = 0
    for char in text_lower:
        if char.isalpha() and char not in vowels:
            consonant_count += 1
            max_consonants = max(max_consonants, consonant_count)
        else:
            consonant_count = 0
    
    if max_consonants > 4:
         return True
    
    # 6. Check Phonotactic Constraints (Quy tắc Âm tiết Tiếng Việt + English Basic)
    # Nếu câu có > 50% từ là "Rác" (OOV - Không đúng cấu trúc) -> Block
    words = text_lower.split()
    valid_word_count = 0
    
    # Định nghĩa sơ bộ cấu trúc Tiếng Việt
    # Nguyen am: a, e, i, o, u, y (va cac bien the dau)
    vowels_set = set("aeiouyàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ")
    
    # Phu am dau (Onsets) hop le
    valid_onsets = ["ch", "gh", "gi", "kh", "ng", "ngh", "nh", "ph", "qu", "th", "tr",
                    "b", "c", "d", "đ", "g", "h", "k", "l", "m", "n", "p", "r", "s", "t", "v", "x"]
                    
    # Phu am cuoi (Codas) hop le
    valid_codas = ["ch", "ng", "nh", 
                   "c", "m", "n", "p", "t", ""] # empty is open syllable
                   
    # Allowlist cho tieng Anh/Teencode co ban (neu regex fail)
    # Hạn chế dùng các chữ đơn lẻ (z, j, f, w) để tránh match nhầm bàn phím (VD: sdfg chứa 'f')
    common_english_clusters = ["ck", "st", "sh", "dm", "ad", "ok", "shop", "ship", "pro", "jack", "ll", "oo", "ee", "ai", "ou", "ea", "ie"]
    single_letter_exceptions = ["z", "j", "f", "w"]
    
    # Common English words allowlist
    common_english_words = {"hello", "hi", "hey", "bye", "thanks", "thank", "you", "please", "sorry", "yes", "no", "ok", "okay", "good", "bad", "nice", "great", "love", "hate", "what", "how", "why", "when", "where", "who", "help", "name", "time", "day", "today", "tomorrow", "yesterday"}

    for w in words:
        is_valid = False
        
        # Rule A: Check Common English / Teencode / Named Entities
        if w in common_english_words or any(c in w for c in common_english_clusters) or w in ["cccd", "bhyt", "vneid", "kcb", "ubnd", "hđnd"]:
            is_valid = True
        elif w in single_letter_exceptions: # Chỉ accept nếu đứng ĐỘC LẬP
            is_valid = True
        
        # Rule B: Check Vietnamese Structure (Simplified)
        # 1. Tu phai co nguyen am
        elif not any(c in vowels_set for c in w):
            is_valid = False # Vowel check failed
        else:
            # Thu kiem tra Onset
            # Tim onset dai nhat khop voi dau tu
            current_onset = ""
            remainder = w
            for onset in sorted(valid_onsets, key=len, reverse=True): # Check 3-char, then 2-char, then 1-char
                if w.startswith(onset):
                    current_onset = onset
                    remainder = w[len(onset):]
                    break
            
            # Sau onset phai la nguyen am
            if not remainder or remainder[0] not in vowels_set:
                 # Neu khong co onset hop le, thu check neu tu bat dau bang nguyen am luon (VD: "an", "o")
                 if w[0] in vowels_set:
                     remainder = w
                 else:
                     is_valid = False
            
            if remainder: # Phan con lai (Van + Coda)
                # Tim coda dai nhat khop voi cuoi tu
                # Luu y: remainder dang chua ca nguyen am + coda (VD: "ang" -> v="a", c="ng")
                # Hacky check: Lay nguyen am het -> phan con lai la Coda
                last_vowel_idx = -1
                for i, char in enumerate(remainder):
                    if char not in vowels_set:
                        # Bat dau thay phu am -> tu day den het la Coda
                        coda_candidate = remainder[i:]
                        if coda_candidate in valid_codas:
                             is_valid = True
                        else:
                             # Coda khong hop le (VD: "k" trong "jack" -> nhung jack da pass o Rule A)
                             # VD: "lg" trong "alg" -> Fail
                             is_valid = False
                        break
                    last_vowel_idx = i
                
                # Neu loop chay het ma toan nguyen am -> Open syllable (Coda rỗng) -> OK
                if last_vowel_idx == len(remainder) - 1:
                    is_valid = True

        if is_valid:
            valid_word_count += 1
            
    # Neu so luong tu hop le thap (< 50%) -> Rác
    # VD: "hgnà álkj kjh" -> 0 valid -> Fail
    # VD: "xin chào jack" -> "xin"(V), "chào"(V), "jack"(E) -> 3/3 -> Pass
    if len(words) > 0:
        valid_ratio = valid_word_count / len(words)
        if valid_ratio < 0.5:
             return True

    # BỎ logic tự động coi tin ngắn là Trivial/Greeting để tránh lưu cache rác (như 'sdahjhpoqwi')
    return False


def should_save_to_cache(user_message, ai_answer, should_search, context_found, history_len):
    """
    Quyết định có nên lưu câu trả lời vào Cache không.
    Chiến lược: "Trust But Verify" + "Safe Context"
    """
    # 0. Anti-Spam / Anti-Gibberish Check (Input Validation)
    # Tái kiểm tra Gibberish để chắc chắn không lưu rác vào cache
    if is_gibberish(user_message):
         return False
    
    # 1. Ưu tiên: Nếu là câu chào hỏi / danh tính -> OK LƯU LUÔN (Context-independent)
    if is_greeting_or_trivial(user_message):
        return True

    # 1.1 Ưu tiên ĐẶC BIỆT: Nếu câu trả lời là Giới thiệu bản thân (có từ khóa xịn) -> OK LƯU LUÔN
    # (Bất chấp search fail hay có history, vì câu giới thiệu danh tính là hằng số)
    ai_lower = ai_answer.lower()
    
    # NEW: Safety Check - Nếu câu trả lời có vẻ là hướng dẫn thủ tục (chứa 'bước', 'hồ sơ', 'làm tại')
    # Thì TUYỆT ĐỐI KHÔNG force cache, kể cả khi có từ 'Trợ lý ảo'.
    # (Chặn trường hợp AI bịa đặt "Tôi là Trợ lý ảo, sau đây là thủ tục..." khi search fail)
    procedural_keywords = ["bước 1", "bước 2", "hồ sơ", "giấy tờ", "lệ phí", "làm tại", "ubnd", "công an"]
    is_procedural = any(pk in ai_lower for pk in procedural_keywords)
    
    if ("trợ lý ảo" in ai_lower or "đông mai số" in ai_lower) and not is_procedural:
         return True
    elif ("trợ lý ảo" in ai_lower) and is_procedural:
         return False
    
    # 1.2 Ưu tiên TUYỆT ĐỐI: Có nguồn tham khảo (Context) -> VERIFY BEFORE APPROVING
    # Ngay cả khi có context, nếu AI lôi "Trợ lý ảo" vào câu trả lời thủ tục -> ĐUỔI THẲNG (Hợp hallucination/Identity leak)
    if context_found:
         # Check Identity Violation: Nếu là câu hỏi thủ tục (phải dùng context) mà AI lại xưng là Trợ lý ảo -> Reject Cache
         identity_leaked = ("trợ lý ảo" in ai_lower or "đông mai số" in ai_lower)
         
         # Check Gibberish in Answer: Từ lạ/ngang tai (VD: "động vấn")
         weird_terms = ["động vấn", "quý động", "vấn quý", "xin chào quý"]
         has_weird_terms = any(wt in ai_lower for wt in weird_terms)
         
         if (identity_leaked and is_procedural) or has_weird_terms:
              return False
              
         return True
         
    # 2. Safety Rule: Nếu là câu hỏi follow-up (đã có lịch sử chat) -> CẤM LƯU
    # (Chỉ áp dụng nếu KHÔNG có context mới. Nếu có context đã return True ở trên rồi)
    if history_len > 0:
        return False

    # 3. Layer 1: Nếu cần Search mà không có Context -> CẤM LƯU
    # (Tránh việc AI "chém gió" khi không có dữ liệu đầu vào)
    if should_search and not context_found:
        return False

    # 4. Layer 2: Nếu câu trả lời chứa từ khóa 'thất bại' -> CẤM LƯU
    bad_keywords = ["xin lỗi", "không tìm thấy", "không có thông tin", 
                    "tôi là trí tuệ nhân tạo", "chưa được cung cấp", 
                    "hệ thống ai đang quá tải", "vui lòng thử lại"]
    ai_lower = ai_answer.lower()
    if any(kw in ai_lower for kw in bad_keywords):
        return False

    # 5. Layer 3: Nếu câu trả lời quá ngắn (nghi vấn lỗi) -> CẤM LƯU
    # Trừ khi là câu giới thiệu bản thân (có từ khóa 'Trợ lý ảo', 'Đông Mai')
    if len(ai_answer) < 50:
        # Nếu là câu giới thiệu bản thân hợp lệ -> CHO QUA
        if "trợ lý ảo" in ai_lower or "đông mai" in ai_lower:
             return True
             
        return False

    # Pass hết các vòng -> HỢP LỆ
    return True



def is_spam_request(session_id):
    """Kiểm tra nếu user gửi tin nhắn quá nhanh (< 3 giây)"""
    try:
        # Lấy tin nhắn cuối cùng của session này
        response = supabase.table("chat_history") \
            .select("created_at") \
            .eq("session_id", session_id) \
            .eq("role", "user") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
            
        if response.data:
            last_msg_time_str = response.data[0]["created_at"] # ISO 8601 string
            # Xử lý ISO string (có thể có hoặc không có giây thập phân)
            try:
                 last_msg_time = datetime.fromisoformat(last_msg_time_str.replace('Z', '+00:00'))
                 now = datetime.now(timezone.utc)
                 delta = now - last_msg_time
                 if delta.total_seconds() < 3:
                     return True
            except ValueError:
                 pass
                 
        return False
    except Exception as e:
        print(f"Spam Check Error: {e}")
        return False

def chat_with_ai(prompt, context, history=[]):
    # System Instruction
    system_prompt = """Bạn là Trợ lý ảo AI của Phường Đông Mai (Quảng Ninh) - "Đông Mai Số".
HÃY TRẢ LỜI TRỰC TIẾP như một tư vấn viên chuyên nghiệp. KHÔNG trình bày các bước suy luận, KHÔNG liệt kê kế hoạch trả lời, KHÔNG ghi chú "Lưu ý: ...".

NHIỆM VỤ: Giải đáp thủ tục hành chính tại phường dựa trên dữ liệu cung cấp.

NGUYÊN TẮC:
    pass
1. **PHẠM VI**: Chỉ trả lời về Phường Đông Mai & thủ tục hành chính. Nếu hỏi việc không liên quan, hãy từ chối lịch sự.
2. **THÁI ĐỘ**: Lễ phép, kính trọng. Xưng "Tôi", gọi dân là "Quý ông/bà" hoặc "Bạn". Dùng "Dạ/Vâng" ở đầu.
3. **TRA CỨU**: Ưu tiên `Dữ liệu tham khảo (Context)`. Nếu không có, dùng kiến thức chung và khuyên liên hệ bộ phận Hành chính công. TUYỆT ĐỐI không bịa đặt số liệu/tên cán bộ/quy trình.
4. **DANH TÍNH (QUAN TRỌNG)**:
   - Nếu hỏi "Bạn là ai?", "Ai tạo ra?" -> BẮT BUỘC dùng cụm từ "Trợ lý ảo" hoặc "Đông Mai Số" để giới thiệu.
   - Nếu hỏi về thủ tục khác (đất đai, kết hôn...) -> CẤM dùng từ "Trợ lý ảo" hay "Đông Mai Số". Hãy trả lời thẳng vào nội dung chuyên môn.
5. **CCCD**: Làm tại Phường Phong Cốc. **VNeID**: Làm tại Công an phường Đông Mai.

THÔNG TIN LIÊN HỆ:
    pass
- Facebook: [Fanpage Phường Đông Mai](https://www.facebook.com/profile.php?id=61578099921000)
- Địa chỉ: Số 15, phố Nghi Tân, khu Tân Mai, phường Đông Mai, Quảng Ninh. SĐT: 02033.580.007

CÁN BỘ CHỦ CHỐT:
    pass
- Ông VŨ NGỌC HÙNG (Chủ tịch phường): 0913.313.928
- Ông PHÙNG VĂN TRỌNG (Chuyên Viên): 0396.629.666
- Bà VŨ THỊ LAN (Chuyên Viên): 0385.328.685"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Nạp lịch sử chat cũ
    if history:
        messages.extend(history)
    
    # Thêm ngữ cảnh mới (nếu có) và câu hỏi hiện tại
    final_user_content = f"Câu hỏi: {prompt}"
    if context:
        final_user_content = f"Dữ liệu tham khảo mới:\n{context}\n\n{final_user_content}"
        
    messages.append({"role": "user", "content": final_user_content})
    
    return ai_router.execute(messages)

# --- SECURITY UTILS ---
SECRET_KEY = os.getenv("SECRET_KEY", "DM_Portal_2026_Secure")  # Load from env, fallback for dev only

# Debug: Print loaded SECRET_KEY

def deobfuscate(payload):
    try:
        # 1. Base64 decode
        decoded = base64.b64decode(payload).decode('utf-8')
        # 2. XOR with key 5 (matching frontend)
        return "".join(chr(ord(c) ^ 5) for c in decoded)
    except Exception as e:
        print(f"Deobfuscation Error: {e}")
        return None

def verify_signature(obfuscated_payload, ts, sig):
    try:
        # Check timestamp drift (max 60s)
        now_ts = int(time.time())
        if abs(now_ts - int(ts)) > 600:
            return False
            
        # Re-calculate hash
        sig_string = f"{ts}{obfuscated_payload}{SECRET_KEY}"
        
        expected = hashlib.sha256(sig_string.encode()).hexdigest()
        if sig != expected:
            pass
            
        return sig == expected
    except Exception as e:
        print(f"Signature Verify Error: {e}")
        return False

def check_ip_rate_limit(ip):
    try:
        now = datetime.now(timezone.utc)
        response = supabase.table("api_rate_limits").select("*").eq("ip", ip).execute()
        
        if response.data:
            record = response.data[0]
            last_request = datetime.fromisoformat(record["last_request_at"].replace('Z', '+00:00'))
            count = record["request_count"]
            
            # Reset if window passed (10 seconds)
            if now - last_request > timedelta(seconds=10):
                supabase.table("api_rate_limits").update({
                    "request_count": 1,
                    "last_request_at": now.isoformat()
                }).eq("ip", ip).execute()
                return True
            
            # Block if > 5 requests in 10s
            if count >= 5:
                return False
                
            # Increment
            supabase.table("api_rate_limits").update({
                "request_count": count + 1,
                "last_request_at": last_request.isoformat() # Keep window start
            }).eq("ip", ip).execute()
        else:
            # First time for this IP
            supabase.table("api_rate_limits").insert({
                "ip": ip,
                "request_count": 1,
                "last_request_at": now.isoformat()
            }).execute()
            
        return True
    except Exception as e:
        print(f"Rate Limit Error: {e}")
        return True # Default to allow if DB fails


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "active", "message": "Chatbot API is running. Use POST to ask questions."}).encode('utf-8'))

    def do_POST(self):
        try:
            # --- LAYER 1: GEOBLOCKING ---
            # Get IP from X-Forwarded-For (Vercel) or client_address
            client_ip = self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
            
            # Check if IP is from allowed country (VN only)
            if not check_geo_allowed(client_ip):
                self.send_response(403)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"answer": "Xin lỗi, dịch vụ này chỉ dành cho người dùng tại Việt Nam."}).encode('utf-8'))
                return

            # --- LAYER 2: IP RATE LIMIT ---
            
            if not check_ip_rate_limit(client_ip):
                self.send_response(429)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"answer": "Phát hiện hoạt động bất thường (Spam). Vui lòng thử lại sau 1 phút."}).encode('utf-8'))
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_json = json.loads(post_data.decode('utf-8'))
            
            # --- LAYER 2: SIGNATURE & OBFUSCATION ---
            obfuscated_msg = request_json.get("p", "") # 'p' for payload (message)
            ts = request_json.get("t", "") # 't' for timestamp
            sig = request_json.get("s", "") # 's' for signature
            obfuscated_sid = request_json.get("sid", "default")
            obfuscated_ctx = request_json.get("c", "")
            
            # Verify Sig
            if not verify_signature(obfuscated_msg, ts, sig):
                self.send_response(403)
                self.end_headers()
                return
            
            # Deobfuscate all
            user_message = deobfuscate(obfuscated_msg)
            session_id = deobfuscate(obfuscated_sid) if obfuscated_sid != "default" else "default"
            provided_context = deobfuscate(obfuscated_ctx) if obfuscated_ctx else ""

            if not user_message or not session_id:
                self.send_response(400)
                self.end_headers()
                return
            
            user_message = user_message.strip()
            
            # 0. Anti-Spam Check
            if is_spam_request(session_id):
                 self.send_response(429)
                 self.send_header('Content-type', 'application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({"answer": "Hệ thống đang bận hoặc bạn gửi tin nhắn quá nhanh. Vui lòng đợi 10 giây."}).encode('utf-8'))
                 return

            # 1. Lấy lịch sử từ Supabase
            history = get_session_history(session_id)
            
            # 1.5 KIỂM TRA TIN NHẮN "TEST" (1 ký tự hoặc symbol)
            # Theo yêu cầu: a, á, à, @, #, v.v. -> Trả lời ngay "Tôi có thể giúp gì"
            clean_msg = user_message.strip()
            if len(clean_msg) == 1 or (len(clean_msg) > 0 and not clean_msg[0].isalnum() and len(clean_msg) < 3):
                 self.send_response(200)
                 self.send_header('Content-type', 'application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({
                     "answer": "Dạ, tôi có thể giúp gì cho bạn về các thủ tục hành chính tại phường Đông Mai không ạ? 😊",
                     "debug": {"cached": False, "test_msg": True}
                 }).encode('utf-8'))
                 return

            # 2. Cache & Search Logic
            # Tối ưu: Dùng helper function để check Greeting/Trivial đồng nhất
            is_trivial_check = is_greeting_or_trivial(user_message)
            
            # 2.1 Anti-Gibberish Check (Chặn Tin Rác ngay lập tức)
            # Nếu là tin rác -> Trả lời ngay, KHÔNG search, KHÔNG AI, KHÔNG Cache.
            if is_gibberish(user_message):
                 self.send_response(400) # Bad Request (hoặc 200 tùy ý)
                 self.send_header('Content-type', 'application/json')
                 self.end_headers()
                 self.wfile.write(json.dumps({
                     "answer": "Dạ, tôi chưa hiểu rõ câu hỏi của bạn. Bạn vui lòng hỏi cụ thể hơn (có dấu, đủ ý) để tôi hỗ trợ nhé! 😊",
                     "debug": {"cached": False, "gibberish": True}
                 }).encode('utf-8'))
                 return
            
            ai_response = None
            is_from_cache = False
            should_search = False  # Initialize to prevent UnboundLocalError
            urls = []
            context = ""
            search_time = 0
            read_time = 0
            should_search = False
            
            # A. KIỂM TRA CACHE TRƯỚC
            # Yêu cầu mới: LUÔN check cache cho TẤT CẢ các câu hỏi (bất kể là câu đầu hay câu sau, chào hỏi hay không)
            # Nếu có trong DB thì trả lời luôn cho nhanh.
            ai_response = get_cached_answer(user_message)
            if ai_response:
                is_from_cache = True
            
            # B. NẾU KHÔNG CÓ CACHE -> TIẾN HÀNH SEARCH VÀ AI
            if not ai_response:
                # Chỉ search nếu KHÔNG phải là câu xã giao/ngắn
                # BỎ điều kiện len(history) == 0 để cho phép search cả câu hỏi follow-up (VD: "Thế còn thủ tục kia?")
                should_search = not is_trivial_check
                
                
                # Tuy nhiên, nếu user đã cung cấp context (VD: chọn file upload), thì không cần Search nữa
                if should_search and not provided_context:
                    start_search = time.time()
                    urls = get_search_results(user_message)
                    search_time = time.time() - start_search
                    
                    # Read
                    start_read = time.time()
                    for url in urls:
                        content = read_web_page(url)
                        if content:
                            context += f"--- Nguồn: {url} ---\n{content[:8000]}\n\n"
                    read_time = time.time() - start_read
                elif provided_context:
                    context = provided_context

                # 3. Gọi AI Chat
                start_chat = time.time()
                ai_response = chat_with_ai(user_message, context, history)
                chat_time = time.time() - start_chat
                
                # Terminology Force: Pre-cache replacement
                ai_response = ai_response.replace("Một cửa", "Hành chính công")
                
                # Lưu vào cache nếu thành công (Dùng Validator xịn)
                # Note: We only approve "High Confidence" if fresh context was found (not empty)
                # context = nội dung thực tế được đưa vào AI, urls = danh sách link
                fresh_context = bool(context and len(context) > 0)
                if should_save_to_cache(user_message, ai_response, should_search, fresh_context, len(history)):
                     save_to_cache(user_message, ai_response)
                else:
                    pass


            else:
                # Cache hit -> chat_time coi như bằng 0
                chat_time = 0
            
            # 4. Lưu lịch sử vào Supabase
            save_message(session_id, "user", user_message)
            if ai_response:
                # Terminology Force: Post-processing final response
                ai_response = ai_response.replace("Một cửa", "Hành chính công")
                save_message(session_id, "assistant", ai_response)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "answer": ai_response,
                "sources": urls,
                "context": context if should_search else None,
                "debug": {
                    "search_time": f"{search_time:.2f}s",
                    "read_time": f"{read_time:.2f}s",
                    "llm_time": f"{chat_time:.2f}s",
                    "cached": is_from_cache
                }
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"SERVER ERROR: {e}")
            self.send_response(500)
            self.end_headers()
        return
