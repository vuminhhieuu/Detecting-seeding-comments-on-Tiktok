# TikTok Crawler - Improved Version

## Tổng quan

Code crawler này được thiết kế để thu thập dữ liệu TikTok một cách toàn diện theo flow:
1. **Video Info** → 2. **All Comments (including replies)** → 3. **User Info** → 4. **Next Video**

## Flow hoạt động CHI TIẾT

### 📹 Với mỗi video URL:

1. **Lấy Video Info** → Lưu ngay vào `tiktok_videos.csv` ✅
2. **Lấy TẤT CẢ Comments** (bao gồm replies) → Lưu ngay vào `tiktok_comments.csv` ✅
3. **Lấy User Info** cho tất cả người comment → Lưu ngay vào `tiktok_users.csv` ✅
4. **Tạo Seeding Dataset** kết hợp → Lưu vào `tiktok_seeding_dataset.csv` ✅
5. **Cập nhật Progress** → Chuyển sang video tiếp theo

## File output

### 1. `tiktok_videos.csv`
Chứa thông tin về các video đã crawl

### 2. `tiktok_comments.csv`
Chứa tất cả comments (bao gồm replies) với các features

### 3. `tiktok_users.csv`
Chứa thông tin chi tiết về users đã comment

### 4. `tiktok_seeding_dataset.csv` ⭐ NEW
File tổng hợp kết hợp dữ liệu từ cả 3 file trên, phục vụ cho việc phân tích seeding comments

### 5. `scraping_progress.json`
Lưu tiến trình crawl để có thể resume khi bị gián đoạn

### 6. `tiktok_scraper.log`
Log chi tiết toàn bộ quá trình crawl

## Monitoring & Logging

### 📊 Real-time Progress Tracking:
- Hiển thị video đang xử lý: `VIDEO 3/10`
- Tiến độ thu thập: `1,234/10,000 comments`
- Tỷ lệ hoàn thành: `12.3%`

### 🔍 Auto Skip Videos:
- Tự động kiểm tra video đã crawl
- Skip video đã có trong database
- Thông báo rõ ràng khi skip

### 📝 Detailed Logging:
```
📹 VIDEO 3/10 - Processing: https://tiktok.com/...
📊 Progress: 1,234/10,000 comments collected
Step 1/4: Getting video info...
💾 Saving video data to tiktok_videos.csv...
✅ Video data saved successfully
Step 2/4: Getting all comments...
📝 Collected 150 comments so far...
```

## Cách sử dụng

### 1. Chuẩn bị
```bash
# Cài đặt dependencies
pip install TikTokApi pandas

# Tạo file video_urls.txt trong thư mục Code
# Mỗi dòng là một URL video TikTok
```

### 2. Cấu hình
Mở file `tiktok_crawler_improved.py` và chỉnh sửa:
```python
# MS Token của bạn
MS_TOKEN = "your_ms_token_here"

# Các thông số crawl
TARGET_COMMENT_COUNT = 10000  # Số comment mục tiêu
MAX_COMMENTS_PER_VIDEO = 1000  # Giới hạn comment/video
MAX_VIDEOS_TO_PROCESS = 300   # Số video tối đa
```

### 3. Chạy crawler
```bash
cd Code
python tiktok_crawler_improved.py
```

### 4. Kiểm tra dữ liệu đã crawl
```bash
# Xem tổng quan
python check_crawled_videos.py

# Kiểm tra video cụ thể
python check_crawled_videos.py <video_id>
```

## Cải tiến so với version cũ

1. **Flow lưu dữ liệu tuần tự**: Lưu ngay sau mỗi bước (không đợi cuối cùng)
2. **Monitoring chi tiết**: Log rõ ràng với emoji và progress tracking
3. **Auto skip videos**: Tự động bỏ qua video đã crawl
4. **Error handling tốt hơn**: Log chi tiết lỗi và tiếp tục với video khác
5. **Progress visualization**: Hiển thị tiến độ dạng X/Y và phần trăm
6. **Check tool**: Script riêng để kiểm tra dữ liệu đã crawl

## Ví dụ Output

```
============================================================
📹 VIDEO 3/10 - Processing: https://www.tiktok.com/@user/video/123
📊 Progress: 1,234/10,000 comments collected
============================================================

Step 1/4: Getting video info...
💾 Saving video data to tiktok_videos.csv...
✅ Video data saved successfully

Step 2/4: Getting all comments for video 123456789...
📝 Collected 50 comments so far...
📝 Collected 100 comments so far...
💾 Saving 127 comments to tiktok_comments.csv...
✅ Comments saved successfully (Total: 127 including replies)

Step 3/4: Getting user info for 89 unique users...
👥 Processed 10/89 users (Failed: 2)
👥 Processed 20/89 users (Failed: 5)
💾 Saving 89 users to tiktok_users.csv...
✅ Users saved successfully (Success: 84, Failed: 5)

Step 4/4: Creating seeding dataset...
💾 Saving seeding dataset to tiktok_seeding_dataset.csv...
✅ Seeding dataset saved successfully

============================================================
✅ VIDEO PROCESSING COMPLETED
📊 Video ID: 123456789
📝 Comments collected: 127 (including replies)
👥 Unique users: 89
📈 Total progress: 1,361/10,000
============================================================

📊 OVERALL PROGRESS:
   Videos processed: 3/10
   Comments collected: 1,361/10,000
   Completion: 13.6%

⏳ Waiting 4.2s before next video...
```

## Troubleshooting

### Lỗi authentication
- Kiểm tra MS_TOKEN còn valid không
- Thử tạo session mới

### Không lấy được reply comments
- TikTokApi có thể không hỗ trợ
- Code sẽ log warning nhưng vẫn tiếp tục

### Rate limit
- Code đã có delay tự động
- Nếu vẫn bị, tăng delay trong code

## Next Steps

1. Phân tích data trong `tiktok_seeding_dataset.csv`
2. Chạy `analyze_seeding_data.py` để phát hiện patterns
3. Train model detect seeding comments 