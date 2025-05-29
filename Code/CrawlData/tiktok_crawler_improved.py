#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import csv
import logging
import json
import pandas as pd
import random
import re
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from TikTokApi import TikTokApi
from TikTokApi.exceptions import *

# --- Configuration ---
TARGET_COMMENT_COUNT = 10000  # Mục tiêu số lượng bình luận cần thu thập
MAX_COMMENTS_PER_VIDEO = 1000  # Giới hạn số bình luận thu thập cho mỗi video (tăng lên để lấy cả replies)
MAX_VIDEOS_TO_PROCESS = 300   # Giới hạn số video xử lý
TIME_RANGE_DAYS = 90          # Chỉ lấy nội dung trong 3 tháng gần đây

# File paths
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Dataset")
os.makedirs(BASE_PATH, exist_ok=True)
VIDEOS_CSV_PATH = os.path.join(BASE_PATH, "tiktok_videos.csv")
COMMENTS_CSV_PATH = os.path.join(BASE_PATH, "tiktok_comments.csv")
USERS_CSV_PATH = os.path.join(BASE_PATH, "tiktok_users.csv")
SEEDING_DATASET_PATH = os.path.join(BASE_PATH, "tiktok_seeding_dataset.csv")
LOG_FILE_PATH = os.path.join(BASE_PATH, "tiktok_scraper.log")
VIDEO_URLS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "video_urls.txt")
PROGRESS_FILE_PATH = os.path.join(BASE_PATH, "scraping_progress.json")

# Authentication - Thay thế bằng msToken của bạn
MS_TOKEN = "XVIBACuK9nYdma2rLPETPsAyU5WJEpYfooh3JM3LOD5jznjJWYE1xHNDoYtDG1J6uya7TPgCTLBWluKQA_6PPUURMwF0H8Qow4WpPamUSY7DCy6wTI_7oGIC-McW6ZvWk5L-0oqmqw1opFU="

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)

# --- CSV Structure ---
video_fieldnames = [
    "video_id", "description", "hashtags", "view_count", "like_count", 
    "share_count", "comment_count", "author_id", "author_nickname", 
    "create_time", "video_link", "music_title", "duration"
]

comment_fieldnames = [
    "comment_id", "video_id", "comment_text", "like_count", "timestamp", 
    "user_id", "user_unique_id", "reply_count", "comment_hash", "text_length",
    "has_emoji", "has_mention", "has_hashtag", "is_reply", "parent_comment_id"
]

user_fieldnames = [
    "user_id", "user_unique_id", "nickname", "followers_count", "following_count", 
    "heart_count", "video_count", "comment_count", "unique_video_count", 
    "duplicate_ratio", "avg_time_between_comments", "account_age_days", 
    "has_profile_picture", "bio_length", "verified", "first_seen", "last_seen",
    "private_account", "friend_count"
]

seeding_fieldnames = [
    # Video fields
    "video_id", "video_description", "video_hashtags", "video_view_count", 
    "video_like_count", "video_share_count", "video_comment_count",
    "video_author_id", "video_author_nickname", "video_create_time",
    # Comment fields
    "comment_id", "comment_text", "comment_like_count", "comment_timestamp",
    "comment_reply_count", "comment_hash", "text_length", "has_emoji", 
    "has_mention", "has_hashtag", "is_reply",
    # User fields
    "user_id", "user_unique_id", "user_nickname", "user_followers_count", 
    "user_following_count", "user_video_count", "user_verified",
    "user_comment_count_in_dataset", "user_duplicate_ratio", 
    "user_avg_time_between_comments"
]

# --- Helper Functions ---
def initialize_csv(filepath, fieldnames):
    """Creates CSV file with header if it doesn't exist."""
    if not os.path.exists(filepath):
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            logging.info(f"Initialized CSV: {filepath}")
        except Exception as e:
            logging.error(f"Failed to initialize CSV {filepath}: {e}")
            return False
    return True

def save_progress(data):
    """Save scraping progress to file"""
    try:
        with open(PROGRESS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save progress: {e}")

def load_progress():
    """Load scraping progress from file"""
    if os.path.exists(PROGRESS_FILE_PATH):
        try:
            with open(PROGRESS_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load progress: {e}")
    return {
        "processed_videos": [],
        "total_comments": 0,
        "total_users": 0
    }

def is_vietnamese_text(text):
    """Enhanced Vietnamese text detection"""
    if not text:
        return False
    
    vietnamese_chars = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệễểìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.IGNORECASE)
    vietnamese_words = ['và', 'của', 'có', 'được', 'không', 'với', 'này', 'cho', 'từ', 'để', 'đã', 'sẽ', 'rất', 'nhiều', 'cũng', 'một', 'hai', 'ba']
    
    has_vietnamese_chars = bool(vietnamese_chars.search(text))
    text_lower = text.lower()
    vietnamese_word_count = sum(1 for word in vietnamese_words if word in text_lower)
    
    return has_vietnamese_chars or vietnamese_word_count >= 2

def calculate_text_features(text):
    """Calculate additional text features for spam detection"""
    if not text:
        return {'text_length': 0, 'has_emoji': False, 'has_mention': False, 'has_hashtag': False}
    
    return {
        'text_length': len(text),
        'has_emoji': bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text)),
        'has_mention': '@' in text,
        'has_hashtag': '#' in text
    }

def load_video_urls():
    """Load video URLs from file"""
    video_urls = []
    if os.path.exists(VIDEO_URLS_PATH):
        try:
            with open(VIDEO_URLS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        video_urls.append(line)
            logging.info(f"Loaded {len(video_urls)} video URLs from {VIDEO_URLS_PATH}")
        except Exception as e:
            logging.error(f"Error loading video URLs: {e}")
    else:
        logging.error(f"Video URLs file not found: {VIDEO_URLS_PATH}")
    
    return video_urls

# --- Data Collection Classes ---
class VideoDataCollector:
    def __init__(self):
        self.video_data = {}
        self.comments_data = []
        self.users_data = {}
        self.user_comments = defaultdict(list)  # Track comments per user
        
    def add_video(self, video_info, video_url):
        """Add video information"""
        author = video_info.get("author", {})
        stats = video_info.get("stats", {})
        
        self.video_data = {
            "video_id": video_info.get("id"),
            "description": video_info.get("desc", ""),
            "hashtags": ",".join([tag.get("hashtagName", "") for tag in video_info.get("textExtra", []) if tag.get("hashtagName")]),
            "view_count": stats.get("playCount", 0),
            "like_count": stats.get("diggCount", 0),
            "share_count": stats.get("shareCount", 0),
            "comment_count": stats.get("commentCount", 0),
            "author_id": author.get("id", ""),
            "author_nickname": author.get("nickname", ""),
            "create_time": datetime.fromtimestamp(int(video_info.get("createTime", 0))).strftime("%Y-%m-%d %H:%M:%S"),
            "video_link": video_url,
            "music_title": video_info.get("music", {}).get("title", ""),
            "duration": video_info.get("duration", 0)
        }
        
    def add_comment(self, comment_dict, video_id, is_reply=False, parent_comment_id=None):
        """Add comment information"""
        comment_text = comment_dict.get("text", "")
        
        if not is_vietnamese_text(comment_text):
            return None
            
        create_time = comment_dict.get("create_time", None)
        if create_time:
            comment_timestamp = datetime.fromtimestamp(int(create_time))
        else:
            comment_timestamp = datetime.now()
        
        text_features = calculate_text_features(comment_text)
        comment_hash = hashlib.md5(comment_text.encode()).hexdigest()
        
        author_info = comment_dict.get("user", {})
        user_id = author_info.get("uid", "")
        user_unique_id = author_info.get("unique_id", "")
        
        comment_data = {
            "comment_id": comment_dict.get("cid", ""),
            "video_id": video_id,
            "comment_text": comment_text,
            "like_count": comment_dict.get("digg_count", 0),
            "timestamp": comment_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "user_unique_id": user_unique_id,
            "reply_count": comment_dict.get("reply_comment_total", 0),
            "comment_hash": comment_hash,
            "text_length": text_features["text_length"],
            "has_emoji": text_features["has_emoji"],
            "has_mention": text_features["has_mention"],
            "has_hashtag": text_features["has_hashtag"],
            "is_reply": is_reply,
            "parent_comment_id": parent_comment_id
        }
        
        self.comments_data.append(comment_data)
        
        # Track user for later fetching
        if user_unique_id and user_unique_id not in self.users_data:
            self.users_data[user_unique_id] = {
                "user_id": user_id,
                "user_unique_id": user_unique_id,
                "nickname": author_info.get("nickname", ""),
                "sec_uid": author_info.get("sec_uid", "")
            }
        
        # Track comments per user
        self.user_comments[user_unique_id].append({
            "text": comment_text,
            "timestamp": comment_timestamp,
            "video_id": video_id
        })
        
        return comment_data
    
    def calculate_user_stats(self, user_unique_id):
        """Calculate user statistics based on their comments"""
        if user_unique_id not in self.user_comments:
            return {}
            
        comments = self.user_comments[user_unique_id]
        
        # Calculate duplicate ratio
        comment_texts = [c["text"] for c in comments]
        comment_hashes = [hashlib.md5(text.encode()).hexdigest() for text in comment_texts]
        unique_comments = len(set(comment_hashes))
        duplicate_ratio = 1 - (unique_comments / len(comments)) if comments else 0
        
        # Calculate average time between comments
        timestamps = sorted([c["timestamp"] for c in comments])
        if len(timestamps) > 1:
            time_diffs = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
            avg_time_between = sum(time_diffs) / len(time_diffs)
        else:
            avg_time_between = 0
        
        # Count unique videos
        unique_videos = len(set([c["video_id"] for c in comments]))
        
        return {
            "comment_count": len(comments),
            "unique_video_count": unique_videos,
            "duplicate_ratio": duplicate_ratio,
            "avg_time_between_comments": avg_time_between,
            "first_seen": min(timestamps).strftime("%Y-%m-%d %H:%M:%S") if timestamps else "",
            "last_seen": max(timestamps).strftime("%Y-%m-%d %H:%M:%S") if timestamps else ""
        }

# --- Main Scraping Function ---
async def get_comment_replies(api, video_id, comment_id, reply_count):
    """Get replies for a specific comment"""
    replies = []
    try:
        # TikTokApi có thể cần một cách khác để lấy replies
        # Đây là một implementation có thể cần điều chỉnh
        # Thử lấy replies thông qua API endpoint khác
        logging.info(f"Attempting to get {reply_count} replies for comment {comment_id}")
        
        # Note: TikTokApi might not have direct support for replies
        # You may need to implement custom logic or use browser automation
        # This is a placeholder that you'll need to adapt based on the API capabilities
        
    except Exception as e:
        logging.warning(f"Could not fetch replies for comment {comment_id}: {e}")
    
    return replies

def check_video_processed(video_id):
    """Check if video has been processed"""
    if os.path.exists(VIDEOS_CSV_PATH):
        try:
            df = pd.read_csv(VIDEOS_CSV_PATH)
            if 'video_id' in df.columns:
                return video_id in df['video_id'].values
        except Exception as e:
            logging.warning(f"Error checking processed videos: {e}")
    return False

async def scrape_video_complete(api, video_url, progress, video_index, total_videos):
    """Scrape complete data for a single video"""
    collector = VideoDataCollector()
    
    try:
        # Step 1: Get video information
        logging.info(f"\n{'='*60}")
        logging.info(f"📹 VIDEO {video_index}/{total_videos} - Processing: {video_url}")
        logging.info(f"📊 Progress: {progress['total_comments']}/{TARGET_COMMENT_COUNT} comments collected")
        logging.info(f"{'='*60}\n")
        
        logging.info(f"Step 1/4: Getting video info...")
        video = api.video(url=video_url)
        video_info = await video.info()
        video_id = video_info.get("id")
        
        if not video_id:
            logging.error(f"❌ Could not get video ID from URL: {video_url}")
            return None
        
        # Check if already processed
        if check_video_processed(video_id):
            logging.info(f"⏭️  Video {video_id} already processed. Skipping...")
            return None
            
        if video_id in progress["processed_videos"]:
            logging.info(f"⏭️  Video {video_id} in progress cache. Skipping...")
            return None
            
        collector.add_video(video_info, video_url)
        
        # Save video data immediately
        logging.info(f"💾 Saving video data to tiktok_videos.csv...")
        with open(VIDEOS_CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=video_fieldnames)
            writer.writerow(collector.video_data)
        logging.info(f"✅ Video data saved successfully")
        
        # Step 2: Get all comments including replies
        logging.info(f"\nStep 2/4: Getting all comments for video {video_id}...")
        comment_count = 0
        comments_with_replies = []  # Store comments that have replies
        
        async for comment in video.comments(count=MAX_COMMENTS_PER_VIDEO):
            comment_dict = comment.as_dict
            
            # Add main comment
            comment_data = collector.add_comment(comment_dict, video_id, is_reply=False)
            if comment_data:
                comment_count += 1
                
                # Check if comment has replies
                reply_count = comment_dict.get("reply_comment_total", 0)
                if reply_count > 0:
                    comments_with_replies.append({
                        'comment_id': comment_dict.get('cid'),
                        'reply_count': reply_count,
                        'comment_dict': comment_dict
                    })
                
                if comment_count % 50 == 0:
                    logging.info(f"📝 Collected {comment_count} comments so far...")
        
        # Step 2.5: Get all replies for comments that have them
        if comments_with_replies:
            logging.info(f"\nStep 2.5/4: Getting replies for {len(comments_with_replies)} comments...")
            
            for idx, comment_info in enumerate(comments_with_replies):
                try:
                    comment_id = comment_info['comment_id']
                    reply_count = comment_info['reply_count']
                    
                    if idx % 10 == 0:
                        logging.info(f"📎 Processing replies: {idx}/{len(comments_with_replies)} comments")
                    
                    # First check if replies are already included in the comment data
                    reply_comment_list = comment_info['comment_dict'].get("reply_comment", [])
                    
                    if reply_comment_list:
                        # If replies are already in the data, process them
                        for reply in reply_comment_list:
                            reply_data = collector.add_comment(
                                reply, 
                                video_id, 
                                is_reply=True, 
                                parent_comment_id=comment_id
                            )
                            if reply_data:
                                comment_count += 1
                    else:
                        # If no replies in data, might need to fetch separately
                        # This depends on TikTokApi capabilities
                        if reply_count > 0:
                            logging.info(f"⚠️  Comment {comment_id} has {reply_count} replies but they're not in the response")
                        
                except Exception as e:
                    logging.warning(f"Error processing replies for comment: {e}")
                    continue
        
        # Save comments data immediately
        logging.info(f"\n💾 Saving {len(collector.comments_data)} comments to tiktok_comments.csv...")
        with open(COMMENTS_CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=comment_fieldnames)
            writer.writerows(collector.comments_data)
        logging.info(f"✅ Comments saved successfully (Total: {comment_count} including replies)")
        
        # Step 3: Get user information for all commenters
        logging.info(f"\nStep 3/4: Getting user info for {len(collector.users_data)} unique users...")
        user_count = 0
        failed_users = 0
        
        for user_unique_id, user_basic_info in collector.users_data.items():
            try:
                # Calculate user stats from comments
                user_stats = collector.calculate_user_stats(user_unique_id)
                user_basic_info.update(user_stats)
                
                # Try to get detailed user info
                try:
                    user_obj = api.user(username=user_unique_id)
                    user_details = await user_obj.info()
                    
                    if user_details:
                        user_info = user_details.get("userInfo", {})
                        stats = user_info.get("stats", {})
                        user_data = user_info.get("user", {})
                        
                        user_basic_info.update({
                            "followers_count": stats.get("followerCount", 0),
                            "following_count": stats.get("followingCount", 0),
                            "heart_count": stats.get("heartCount", 0),
                            "video_count": stats.get("videoCount", 0),
                            "friend_count": stats.get("friendCount", 0),
                            "bio_length": len(user_data.get("signature", "")),
                            "verified": user_data.get("verified", False),
                            "private_account": user_data.get("privateAccount", False),
                            "has_profile_picture": bool(user_data.get("avatarLarger", "")),
                            "account_age_days": (datetime.now() - datetime.fromtimestamp(
                                user_data.get("createTime", datetime.now().timestamp())
                            )).days if user_data.get("createTime") else 0
                        })
                        
                except Exception as e:
                    failed_users += 1
                    logging.warning(f"⚠️  Could not get detailed info for user {user_unique_id}: {e}")
                
                user_count += 1
                if user_count % 10 == 0:
                    logging.info(f"👥 Processed {user_count}/{len(collector.users_data)} users (Failed: {failed_users})")
                    
                # Add delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logging.error(f"❌ Error processing user {user_unique_id}: {e}")
                continue
        
        # Save users data immediately
        logging.info(f"\n💾 Saving {len(collector.users_data)} users to tiktok_users.csv...")
        users_to_save = []
        for user_unique_id, user_data in collector.users_data.items():
            user_record = {field: user_data.get(field, "") for field in user_fieldnames}
            users_to_save.append(user_record)
        
        with open(USERS_CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=user_fieldnames)
            writer.writerows(users_to_save)
        logging.info(f"✅ Users saved successfully (Success: {user_count - failed_users}, Failed: {failed_users})")
        
        # Step 4: Save to seeding dataset (combined data)
        logging.info(f"\nStep 4/4: Creating seeding dataset...")
        seeding_records = []
        for comment in collector.comments_data:
            user_data = collector.users_data.get(comment["user_unique_id"], {})
            
            seeding_record = {
                # Video fields
                "video_id": collector.video_data["video_id"],
                "video_description": collector.video_data["description"],
                "video_hashtags": collector.video_data["hashtags"],
                "video_view_count": collector.video_data["view_count"],
                "video_like_count": collector.video_data["like_count"],
                "video_share_count": collector.video_data["share_count"],
                "video_comment_count": collector.video_data["comment_count"],
                "video_author_id": collector.video_data["author_id"],
                "video_author_nickname": collector.video_data["author_nickname"],
                "video_create_time": collector.video_data["create_time"],
                # Comment fields
                "comment_id": comment["comment_id"],
                "comment_text": comment["comment_text"],
                "comment_like_count": comment["like_count"],
                "comment_timestamp": comment["timestamp"],
                "comment_reply_count": comment["reply_count"],
                "comment_hash": comment["comment_hash"],
                "text_length": comment["text_length"],
                "has_emoji": comment["has_emoji"],
                "has_mention": comment["has_mention"],
                "has_hashtag": comment["has_hashtag"],
                "is_reply": comment["is_reply"],
                # User fields
                "user_id": user_data.get("user_id", ""),
                "user_unique_id": user_data.get("user_unique_id", ""),
                "user_nickname": user_data.get("nickname", ""),
                "user_followers_count": user_data.get("followers_count", 0),
                "user_following_count": user_data.get("following_count", 0),
                "user_video_count": user_data.get("video_count", 0),
                "user_verified": user_data.get("verified", False),
                "user_comment_count_in_dataset": user_data.get("comment_count", 0),
                "user_duplicate_ratio": user_data.get("duplicate_ratio", 0),
                "user_avg_time_between_comments": user_data.get("avg_time_between_comments", 0)
            }
            seeding_records.append(seeding_record)
        
        logging.info(f"💾 Saving seeding dataset to tiktok_seeding_dataset.csv...")
        with open(SEEDING_DATASET_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=seeding_fieldnames)
            writer.writerows(seeding_records)
        logging.info(f"✅ Seeding dataset saved successfully")
        
        # Summary
        logging.info(f"\n{'='*60}")
        logging.info(f"✅ VIDEO PROCESSING COMPLETED")
        logging.info(f"📊 Video ID: {video_id}")
        logging.info(f"📝 Comments collected: {comment_count} (including replies)")
        logging.info(f"👥 Unique users: {len(collector.users_data)}")
        logging.info(f"📈 Total progress: {progress['total_comments'] + comment_count}/{TARGET_COMMENT_COUNT}")
        logging.info(f"{'='*60}\n")
        
        return collector
        
    except Exception as e:
        logging.error(f"❌ Fatal error processing video {video_url}: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None

async def save_collected_data(collector):
    """This function is no longer needed as we save data immediately"""
    # Kept for compatibility but not used
    return True

async def main():
    """Main function to orchestrate the scraping process"""
    # Initialize CSV files
    initialize_csv(VIDEOS_CSV_PATH, video_fieldnames)
    initialize_csv(COMMENTS_CSV_PATH, comment_fieldnames)
    initialize_csv(USERS_CSV_PATH, user_fieldnames)
    initialize_csv(SEEDING_DATASET_PATH, seeding_fieldnames)
    
    # Load progress
    progress = load_progress()
    
    # Load video URLs
    video_urls = load_video_urls()
    if not video_urls:
        logging.error("❌ No video URLs found. Please add URLs to video_urls.txt")
        return
    
    # Print initial status
    logging.info(f"\n{'='*80}")
    logging.info(f"🚀 TIKTOK CRAWLER STARTING")
    logging.info(f"📊 Target: {TARGET_COMMENT_COUNT} comments")
    logging.info(f"📹 Videos to process: {len(video_urls)}")
    logging.info(f"💾 Resume from: {progress['total_comments']} comments")
    logging.info(f"{'='*80}\n")
    
    # Initialize API
    async with TikTokApi() as api:
        logging.info("🌐 Creating browser session...")
        try:
            await api.create_sessions(
                ms_tokens=[MS_TOKEN] if MS_TOKEN else None,
                num_sessions=1,
                sleep_after=3,
                headless=True,
                browser="chromium"
            )
            logging.info("✅ Browser session created successfully.")
        except Exception as e:
            logging.error(f"❌ Failed to create browser session: {e}")
            return
        
        # Process videos
        total_comments = progress["total_comments"]
        videos_processed = len(progress["processed_videos"])
        
        for idx, video_url in enumerate(video_urls):
            if total_comments >= TARGET_COMMENT_COUNT:
                logging.info(f"\n🎯 Reached target comment count ({TARGET_COMMENT_COUNT}). Stopping.")
                break
                
            if videos_processed >= MAX_VIDEOS_TO_PROCESS:
                logging.info(f"\n🛑 Reached maximum videos to process ({MAX_VIDEOS_TO_PROCESS}). Stopping.")
                break
            
            # Scrape complete data for this video
            collector = await scrape_video_complete(api, video_url, progress, idx+1, len(video_urls))
            
            if collector:
                # Update progress
                progress["processed_videos"].append(collector.video_data["video_id"])
                progress["total_comments"] += len(collector.comments_data)
                progress["total_users"] += len(collector.users_data)
                total_comments = progress["total_comments"]
                videos_processed += 1
                
                save_progress(progress)
                
                # Log overall progress
                logging.info(f"\n📊 OVERALL PROGRESS:")
                logging.info(f"   Videos processed: {videos_processed}/{min(len(video_urls), MAX_VIDEOS_TO_PROCESS)}")
                logging.info(f"   Comments collected: {total_comments}/{TARGET_COMMENT_COUNT}")
                logging.info(f"   Completion: {(total_comments/TARGET_COMMENT_COUNT)*100:.1f}%")
            
            # Add delay between videos
            if idx < len(video_urls) - 1 and total_comments < TARGET_COMMENT_COUNT:
                delay = random.uniform(3, 5)
                logging.info(f"\n⏳ Waiting {delay:.1f}s before next video...")
                await asyncio.sleep(delay)
    
    # Final summary
    logging.info(f"\n{'='*80}")
    logging.info(f"🎉 SCRAPING COMPLETED!")
    logging.info(f"📹 Total videos processed: {len(progress['processed_videos'])}")
    logging.info(f"📝 Total comments collected: {progress['total_comments']}")
    logging.info(f"👥 Total unique users: {progress['total_users']}")
    logging.info(f"📁 Data saved in: {BASE_PATH}")
    logging.info(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main()) 