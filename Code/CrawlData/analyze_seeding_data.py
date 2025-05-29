#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# File path
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Dataset")
SEEDING_DATASET_PATH = os.path.join(BASE_PATH, "tiktok_seeding_dataset.csv")

def load_data():
    """Load the seeding dataset"""
    try:
        df = pd.read_csv(SEEDING_DATASET_PATH)
        print(f"Loaded {len(df)} records from seeding dataset")
        return df
    except FileNotFoundError:
        print(f"File not found: {SEEDING_DATASET_PATH}")
        print("Please run the crawler first to generate data")
        return None

def analyze_user_patterns(df):
    """Analyze user behavior patterns that might indicate seeding"""
    print("\n=== USER BEHAVIOR ANALYSIS ===")
    
    # Users with high duplicate ratio
    high_duplicate_users = df[df['user_duplicate_ratio'] > 0.5]
    print(f"\nUsers with >50% duplicate comments: {high_duplicate_users['user_unique_id'].nunique()}")
    
    # Users commenting on multiple videos
    user_video_counts = df.groupby('user_unique_id')['video_id'].nunique()
    multi_video_users = user_video_counts[user_video_counts > 3]
    print(f"Users commenting on >3 videos: {len(multi_video_users)}")
    
    # Users with suspiciously fast commenting
    fast_commenters = df[df['user_avg_time_between_comments'] < 60]  # Less than 1 minute
    print(f"Users with avg time between comments <1 min: {fast_commenters['user_unique_id'].nunique()}")
    
    # New accounts with high activity
    new_active_users = df[(df['user_followers_count'] < 100) & (df['user_comment_count_in_dataset'] > 10)]
    print(f"New accounts (<100 followers) with >10 comments: {new_active_users['user_unique_id'].nunique()}")
    
    return {
        'high_duplicate_users': high_duplicate_users,
        'multi_video_users': multi_video_users,
        'fast_commenters': fast_commenters,
        'new_active_users': new_active_users
    }

def analyze_comment_patterns(df):
    """Analyze comment text patterns"""
    print("\n=== COMMENT PATTERN ANALYSIS ===")
    
    # Short generic comments (potential spam)
    short_comments = df[df['text_length'] < 20]
    print(f"\nVery short comments (<20 chars): {len(short_comments)} ({len(short_comments)/len(df)*100:.1f}%)")
    
    # Comments with only emojis
    emoji_only = df[(df['has_emoji'] == True) & (df['text_length'] < 10)]
    print(f"Comments with mostly emojis: {len(emoji_only)} ({len(emoji_only)/len(df)*100:.1f}%)")
    
    # Generic praise patterns
    generic_phrases = ['hay quá', 'tuyệt vời', 'quá đỉnh', 'xuất sắc', 'ok', 'good', 'nice']
    generic_mask = df['comment_text'].str.lower().str.contains('|'.join(generic_phrases), na=False)
    generic_comments = df[generic_mask]
    print(f"Comments with generic praise: {len(generic_comments)} ({len(generic_comments)/len(df)*100:.1f}%)")
    
    # Duplicate comments across videos
    duplicate_texts = df.groupby('comment_hash').agg({
        'video_id': 'nunique',
        'user_unique_id': 'count'
    })
    cross_video_duplicates = duplicate_texts[duplicate_texts['video_id'] > 1]
    print(f"Identical comments across multiple videos: {len(cross_video_duplicates)}")
    
    return {
        'short_comments': short_comments,
        'emoji_only': emoji_only,
        'generic_comments': generic_comments,
        'cross_video_duplicates': cross_video_duplicates
    }

def calculate_seeding_score(row):
    """Calculate a seeding probability score for each comment"""
    score = 0
    
    # User-based factors
    if row['user_duplicate_ratio'] > 0.5:
        score += 20
    if row['user_comment_count_in_dataset'] > 10 and row['user_followers_count'] < 100:
        score += 15
    if row['user_avg_time_between_comments'] < 60:
        score += 15
    
    # Comment-based factors
    if row['text_length'] < 20:
        score += 10
    if row['has_emoji'] and row['text_length'] < 10:
        score += 10
    if not row['has_mention'] and not row['has_hashtag']:
        score += 5
    
    # Video interaction patterns
    if row['user_video_count'] > 5:
        score += 10
    
    # Normalize to 0-100
    return min(score, 100)

def visualize_patterns(df, suspicious_patterns):
    """Create visualizations of seeding patterns"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. User duplicate ratio distribution
    ax1 = axes[0, 0]
    df['user_duplicate_ratio'].hist(bins=20, ax=ax1)
    ax1.set_title('Distribution of User Duplicate Comment Ratio')
    ax1.set_xlabel('Duplicate Ratio')
    ax1.set_ylabel('Number of Users')
    ax1.axvline(x=0.5, color='r', linestyle='--', label='Suspicious threshold')
    ax1.legend()
    
    # 2. Comment length distribution
    ax2 = axes[0, 1]
    df['text_length'].hist(bins=30, ax=ax2, range=(0, 200))
    ax2.set_title('Distribution of Comment Length')
    ax2.set_xlabel('Text Length (characters)')
    ax2.set_ylabel('Number of Comments')
    ax2.axvline(x=20, color='r', linestyle='--', label='Short comment threshold')
    ax2.legend()
    
    # 3. Time between comments
    ax3 = axes[1, 0]
    time_data = df[df['user_avg_time_between_comments'] > 0]['user_avg_time_between_comments']
    time_data = time_data[time_data < 3600]  # Only show first hour for clarity
    time_data.hist(bins=30, ax=ax3)
    ax3.set_title('Average Time Between User Comments')
    ax3.set_xlabel('Time (seconds)')
    ax3.set_ylabel('Number of Users')
    ax3.axvline(x=60, color='r', linestyle='--', label='Suspicious threshold')
    ax3.legend()
    
    # 4. Seeding score distribution
    ax4 = axes[1, 1]
    df['seeding_score'].hist(bins=20, ax=ax4)
    ax4.set_title('Distribution of Seeding Probability Scores')
    ax4.set_xlabel('Seeding Score (0-100)')
    ax4.set_ylabel('Number of Comments')
    ax4.axvline(x=50, color='r', linestyle='--', label='High risk threshold')
    ax4.legend()
    
    plt.tight_layout()
    output_path = os.path.join(BASE_PATH, 'seeding_analysis_plots.png')
    plt.savefig(output_path)
    print(f"\nVisualizations saved to: {output_path}")
    plt.close()

def generate_report(df, user_patterns, comment_patterns):
    """Generate a summary report of potential seeding activity"""
    report_path = os.path.join(BASE_PATH, 'seeding_analysis_report.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("TIKTOK SEEDING ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Comments Analyzed: {len(df)}\n")
        f.write(f"Total Users: {df['user_unique_id'].nunique()}\n")
        f.write(f"Total Videos: {df['video_id'].nunique()}\n\n")
        
        f.write("SUSPICIOUS USER PATTERNS\n")
        f.write("-" * 30 + "\n")
        f.write(f"High duplicate ratio users: {user_patterns['high_duplicate_users']['user_unique_id'].nunique()}\n")
        f.write(f"Multi-video commenters: {len(user_patterns['multi_video_users'])}\n")
        f.write(f"Fast commenters: {user_patterns['fast_commenters']['user_unique_id'].nunique()}\n")
        f.write(f"New accounts with high activity: {user_patterns['new_active_users']['user_unique_id'].nunique()}\n\n")
        
        f.write("SUSPICIOUS COMMENT PATTERNS\n")
        f.write("-" * 30 + "\n")
        f.write(f"Very short comments: {len(comment_patterns['short_comments'])}\n")
        f.write(f"Emoji-only comments: {len(comment_patterns['emoji_only'])}\n")
        f.write(f"Generic praise comments: {len(comment_patterns['generic_comments'])}\n")
        f.write(f"Cross-video duplicates: {len(comment_patterns['cross_video_duplicates'])}\n\n")
        
        # High risk comments
        high_risk = df[df['seeding_score'] >= 50]
        f.write(f"HIGH RISK COMMENTS (Score >= 50)\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total high risk comments: {len(high_risk)} ({len(high_risk)/len(df)*100:.1f}%)\n\n")
        
        # Top suspicious users
        f.write("TOP 10 MOST SUSPICIOUS USERS\n")
        f.write("-" * 30 + "\n")
        user_scores = df.groupby('user_unique_id')['seeding_score'].mean().sort_values(ascending=False)
        for i, (user, score) in enumerate(user_scores.head(10).items()):
            user_data = df[df['user_unique_id'] == user].iloc[0]
            f.write(f"{i+1}. {user} (Score: {score:.1f})\n")
            f.write(f"   - Comments: {user_data['user_comment_count_in_dataset']}\n")
            f.write(f"   - Duplicate ratio: {user_data['user_duplicate_ratio']:.2f}\n")
            f.write(f"   - Followers: {user_data['user_followers_count']}\n\n")
    
    print(f"\nDetailed report saved to: {report_path}")

def main():
    """Main analysis function"""
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Calculate seeding scores
    print("\nCalculating seeding probability scores...")
    df['seeding_score'] = df.apply(calculate_seeding_score, axis=1)
    
    # Analyze patterns
    user_patterns = analyze_user_patterns(df)
    comment_patterns = analyze_comment_patterns(df)
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    visualize_patterns(df, {'user_patterns': user_patterns, 'comment_patterns': comment_patterns})
    
    # Generate report
    print("\nGenerating detailed report...")
    generate_report(df, user_patterns, comment_patterns)
    
    # Summary statistics
    print("\n=== SUMMARY ===")
    high_risk = df[df['seeding_score'] >= 50]
    print(f"Total high-risk comments: {len(high_risk)} ({len(high_risk)/len(df)*100:.1f}%)")
    print(f"Unique high-risk users: {high_risk['user_unique_id'].nunique()}")
    print(f"Average seeding score: {df['seeding_score'].mean():.1f}")
    
    # Export high risk comments
    high_risk_path = os.path.join(BASE_PATH, 'high_risk_comments.csv')
    high_risk.to_csv(high_risk_path, index=False)
    print(f"\nHigh risk comments exported to: {high_risk_path}")

if __name__ == "__main__":
    main() 