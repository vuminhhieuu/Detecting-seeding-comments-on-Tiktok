#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import json

# File paths
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Dataset")
VIDEOS_CSV_PATH = os.path.join(BASE_PATH, "tiktok_videos.csv")
COMMENTS_CSV_PATH = os.path.join(BASE_PATH, "tiktok_comments.csv")
USERS_CSV_PATH = os.path.join(BASE_PATH, "tiktok_users.csv")
SEEDING_DATASET_PATH = os.path.join(BASE_PATH, "tiktok_seeding_dataset.csv")
PROGRESS_FILE_PATH = os.path.join(BASE_PATH, "scraping_progress.json")

def check_crawled_data():
    """Check status of crawled data"""
    print("="*60)
    print("📊 TIKTOK CRAWLER DATA STATUS")
    print("="*60)
    
    # Check videos
    if os.path.exists(VIDEOS_CSV_PATH):
        df_videos = pd.read_csv(VIDEOS_CSV_PATH)
        print(f"\n📹 VIDEOS:")
        print(f"   Total videos crawled: {len(df_videos)}")
        if len(df_videos) > 0:
            print(f"   Video IDs: {df_videos['video_id'].tolist()[:5]}..." if len(df_videos) > 5 else f"   Video IDs: {df_videos['video_id'].tolist()}")
    else:
        print(f"\n📹 VIDEOS: No data yet")
    
    # Check comments
    if os.path.exists(COMMENTS_CSV_PATH):
        df_comments = pd.read_csv(COMMENTS_CSV_PATH)
        print(f"\n📝 COMMENTS:")
        print(f"   Total comments: {len(df_comments)}")
        print(f"   Main comments: {len(df_comments[df_comments['is_reply'] == False])}")
        print(f"   Reply comments: {len(df_comments[df_comments['is_reply'] == True])}")
    else:
        print(f"\n📝 COMMENTS: No data yet")
    
    # Check users
    if os.path.exists(USERS_CSV_PATH):
        df_users = pd.read_csv(USERS_CSV_PATH)
        print(f"\n👥 USERS:")
        print(f"   Total unique users: {len(df_users)}")
        if len(df_users) > 0:
            verified_users = len(df_users[df_users['verified'] == True])
            print(f"   Verified users: {verified_users}")
    else:
        print(f"\n👥 USERS: No data yet")
    
    # Check seeding dataset
    if os.path.exists(SEEDING_DATASET_PATH):
        df_seeding = pd.read_csv(SEEDING_DATASET_PATH)
        print(f"\n🎯 SEEDING DATASET:")
        print(f"   Total records: {len(df_seeding)}")
    else:
        print(f"\n🎯 SEEDING DATASET: No data yet")
    
    # Check progress
    if os.path.exists(PROGRESS_FILE_PATH):
        with open(PROGRESS_FILE_PATH, 'r') as f:
            progress = json.load(f)
        print(f"\n📈 PROGRESS:")
        print(f"   Processed video IDs: {progress.get('processed_videos', [])[:5]}..." if len(progress.get('processed_videos', [])) > 5 else f"   Processed video IDs: {progress.get('processed_videos', [])}")
        print(f"   Total comments in progress: {progress.get('total_comments', 0)}")
        print(f"   Total users in progress: {progress.get('total_users', 0)}")
    
    print("\n" + "="*60)

def check_video_exists(video_id):
    """Check if a specific video has been crawled"""
    if os.path.exists(VIDEOS_CSV_PATH):
        df_videos = pd.read_csv(VIDEOS_CSV_PATH)
        if video_id in df_videos['video_id'].values:
            video_data = df_videos[df_videos['video_id'] == video_id].iloc[0]
            print(f"\n✅ Video {video_id} has been crawled:")
            print(f"   Description: {video_data['description'][:100]}...")
            print(f"   Views: {video_data['view_count']:,}")
            print(f"   Comments: {video_data['comment_count']:,}")
            return True
        else:
            print(f"\n❌ Video {video_id} has NOT been crawled")
            return False
    else:
        print(f"\n❌ No video data found")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Check specific video
        video_id = sys.argv[1]
        check_video_exists(video_id)
    else:
        # Show general status
        check_crawled_data()
        
        print("\n💡 TIP: To check a specific video, run:")
        print("   python check_crawled_videos.py <video_id>") 