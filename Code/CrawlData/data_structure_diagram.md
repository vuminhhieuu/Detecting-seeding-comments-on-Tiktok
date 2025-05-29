# Cấu trúc dữ liệu TikTok Crawler

## 📁 Cấu trúc thư mục

```
Detecting-seeding-comments-on-Tiktok/
├── Code/
│   ├── tiktok_crawler_improved.py
│   ├── analyze_seeding_data.py
│   ├── video_urls.txt
│   └── README_crawler.md
├── Dataset/                    # Tất cả dữ liệu được lưu ở đây
│   ├── tiktok_videos.csv      # Thông tin video
│   ├── tiktok_comments.csv    # Thông tin comments
│   ├── tiktok_users.csv       # Thông tin users
│   ├── tiktok_seeding_dataset.csv  # File tổng hợp (NEW)
│   ├── tiktok_scraper.log     # Log file
│   └── scraping_progress.json  # Progress tracking
└── Document/
```

## 📊 Chi tiết các file CSV

### 1. `tiktok_videos.csv`
Lưu thông tin của mỗi video đã crawl:
- video_id
- description
- hashtags
- view_count, like_count, share_count, comment_count
- author_id, author_nickname
- create_time, video_link
- music_title, duration

### 2. `tiktok_comments.csv`
Lưu TẤT CẢ comments (bao gồm cả replies):
- comment_id, video_id
- comment_text
- like_count, timestamp
- user_id, user_unique_id
- reply_count, comment_hash
- text_length, has_emoji, has_mention, has_hashtag
- is_reply, parent_comment_id

### 3. `tiktok_users.csv`
Lưu thông tin chi tiết của users đã comment:
- user_id, user_unique_id, nickname
- followers_count, following_count
- heart_count, video_count
- comment_count, unique_video_count
- duplicate_ratio, avg_time_between_comments
- account_age_days, has_profile_picture
- bio_length, verified
- first_seen, last_seen
- private_account, friend_count

### 4. `tiktok_seeding_dataset.csv` ⭐
File tổng hợp kết hợp dữ liệu từ cả 3 file trên cho mỗi comment:
- Tất cả fields từ video (với prefix "video_")
- Tất cả fields từ comment (với prefix "comment_")
- Tất cả fields từ user (với prefix "user_")

## 🔄 Flow crawl data

```
1. Load video URL
       ↓
2. Get Video Info → Save to tiktok_videos.csv
       ↓
3. Get ALL Comments (including replies)
       ↓
4. For each comment:
   - Extract comment data → Save to tiktok_comments.csv
   - Track user info
       ↓
5. For each unique user:
   - Calculate user stats
   - Get detailed user profile → Save to tiktok_users.csv
       ↓
6. Combine all data → Save to tiktok_seeding_dataset.csv
       ↓
7. Update progress → Save to scraping_progress.json
       ↓
8. Move to next video (repeat from step 1)
```

## 📝 Log structure

File `tiktok_scraper.log` ghi lại:
- Timestamp của mỗi action
- Video đang xử lý
- Số lượng comments đã thu thập
- Errors và warnings
- Progress updates

## 🔧 Điểm khác biệt với code cũ

1. **Flow tuần tự nghiêm ngặt**: Phải hoàn thành TOÀN BỘ data của 1 video mới chuyển sang video khác
2. **Reply comments**: Code chuẩn bị sẵn logic để lấy reply comments
3. **File tổng hợp mới**: `tiktok_seeding_dataset.csv` giúp phân tích dễ dàng hơn
4. **Progress tracking**: Có thể resume khi bị gián đoạn
5. **User statistics**: Tính toán metrics quan trọng cho việc detect seeding 