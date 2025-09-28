#!/usr/bin/env python3
"""
Demographic Analysis and Visualization
Behavioral Biometrics Study - EDA and Statistical Analysis

This script generates comprehensive demographic analysis and visualizations
for a research paper on behavioral biometrics and keystroke dynamics.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Configure matplotlib for publication quality
plt.rcParams.update({
    'figure.figsize': (12, 8),
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 16,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'axes.grid': True,
    'grid.alpha': 0.3,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

def load_and_preprocess_data(file_path):
    """Load and preprocess the metadata CSV file."""
    print("Loading and preprocessing data...")
    
    # Load the data
    df = pd.read_csv(file_path)
    
    # Convert timestamps
    df['submission_timestamp'] = pd.to_datetime(df['submission_timestamp'], errors='coerce')
    df['consent_timestamp'] = pd.to_datetime(df['consent_timestamp'], errors='coerce')
    
    # Calculate study duration
    df['study_duration_minutes'] = (df['submission_timestamp'] - df['consent_timestamp']).dt.total_seconds() / 60
    
    # Clean age groups for better visualization
    df['age_group'] = df['age'].replace({
        '18_24': '18-24',
        '25_34': '25-34', 
        '35_44': '35-44',
        '45_54': '45-54',
        '55_64': '55-64'
    })
    
    # Clean education levels
    df['education_level'] = df['education'].replace({
        'high_school': 'High School',
        'some_college': 'Some College',
        'bachelor': "Bachelor's",
        'masters': "Master's",
        'doctorate': 'Doctorate'
    })
    
    # Extract browser information
    df['browser'] = df['user_agent'].str.extract(r'(Chrome|Firefox|Safari|Edge)')
    df['browser'] = df['browser'].fillna('Other')
    
    # Extract OS information
    df['os'] = 'Windows'
    df.loc[df['user_agent'].str.contains('Macintosh', na=False), 'os'] = 'macOS'
    df.loc[df['user_agent'].str.contains('Linux', na=False), 'os'] = 'Linux'
    df.loc[df['user_agent'].str.contains('Android', na=False), 'os'] = 'Android'
    
    # Calculate screen area
    df['screen_area'] = df['screen_width'] * df['screen_height']
    df['window_area'] = df['window_width'] * df['window_height']
    
    # Separate complete and broken participants
    complete_df = df[df['status'] == 'complete'].copy()
    broken_df = df[df['status'] == 'broken'].copy()
    
    print(f"Total participants: {len(df)}")
    print(f"Complete participants: {len(complete_df)}")
    print(f"Broken/incomplete participants: {len(broken_df)}")
    print(f"Completion rate: {len(complete_df)/len(df)*100:.1f}%")
    
    return df, complete_df, broken_df

def create_demographic_overview(complete_df, broken_df):
    """Create comprehensive demographic overview visualizations."""
    print("\nCreating demographic overview...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Demographic Overview of Study Participants', fontsize=16, fontweight='bold')
    
    # 1. Gender Distribution
    gender_complete = complete_df['gender'].value_counts()
    gender_broken = broken_df['gender'].value_counts()
    
    ax1 = axes[0, 0]
    x = np.arange(len(gender_complete))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, gender_complete.values, width, label='Complete', alpha=0.8)
    bars2 = ax1.bar(x + width/2, gender_broken.values, width, label='Broken', alpha=0.8)
    
    ax1.set_xlabel('Gender')
    ax1.set_ylabel('Number of Participants')
    ax1.set_title('Gender Distribution by Study Completion Status')
    ax1.set_xticks(x)
    ax1.set_xticklabels(gender_complete.index)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom')
    for bar in bars2:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom')
    
    # 2. Age Distribution
    age_complete = complete_df['age_group'].value_counts().sort_index()
    age_broken = broken_df['age_group'].value_counts().sort_index()
    
    ax2 = axes[0, 1]
    x = np.arange(len(age_complete))
    bars1 = ax2.bar(x - width/2, age_complete.values, width, label='Complete', alpha=0.8)
    bars2 = ax2.bar(x + width/2, age_broken.values, width, label='Broken', alpha=0.8)
    
    ax2.set_xlabel('Age Group')
    ax2.set_ylabel('Number of Participants')
    ax2.set_title('Age Distribution by Study Completion Status')
    ax2.set_xticks(x)
    ax2.set_xticklabels(age_complete.index, rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Education Distribution
    edu_complete = complete_df['education_level'].value_counts()
    edu_broken = broken_df['education_level'].value_counts()
    
    ax3 = axes[0, 2]
    x = np.arange(len(edu_complete))
    bars1 = ax3.bar(x - width/2, edu_complete.values, width, label='Complete', alpha=0.8)
    bars2 = ax3.bar(x + width/2, edu_broken.values, width, label='Broken', alpha=0.8)
    
    ax3.set_xlabel('Education Level')
    ax3.set_ylabel('Number of Participants')
    ax3.set_title('Education Distribution by Study Completion Status')
    ax3.set_xticks(x)
    ax3.set_xticklabels(edu_complete.index, rotation=45)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Handedness Distribution
    handed_complete = complete_df['handedness'].value_counts()
    handed_broken = broken_df['handedness'].value_counts()
    
    ax4 = axes[1, 0]
    x = np.arange(len(handed_complete))
    bars1 = ax4.bar(x - width/2, handed_complete.values, width, label='Complete', alpha=0.8)
    bars2 = ax4.bar(x + width/2, handed_broken.values, width, label='Broken', alpha=0.8)
    
    ax4.set_xlabel('Handedness')
    ax4.set_ylabel('Number of Participants')
    ax4.set_title('Handedness Distribution by Study Completion Status')
    ax4.set_xticks(x)
    ax4.set_xticklabels(handed_complete.index)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Browser Distribution
    browser_complete = complete_df['browser'].value_counts()
    browser_broken = broken_df['browser'].value_counts()
    
    # Get all unique browsers
    all_browsers = set(browser_complete.index) | set(browser_broken.index)
    all_browsers = sorted(list(all_browsers))
    
    # Align the data
    complete_counts = [browser_complete.get(browser, 0) for browser in all_browsers]
    broken_counts = [browser_broken.get(browser, 0) for browser in all_browsers]
    
    ax5 = axes[1, 1]
    x = np.arange(len(all_browsers))
    bars1 = ax5.bar(x - width/2, complete_counts, width, label='Complete', alpha=0.8)
    bars2 = ax5.bar(x + width/2, broken_counts, width, label='Broken', alpha=0.8)
    
    ax5.set_xlabel('Browser')
    ax5.set_ylabel('Number of Participants')
    ax5.set_title('Browser Distribution by Study Completion Status')
    ax5.set_xticks(x)
    ax5.set_xticklabels(all_browsers)
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Operating System Distribution
    os_complete = complete_df['os'].value_counts()
    os_broken = broken_df['os'].value_counts()
    
    # Get all unique OS
    all_os = set(os_complete.index) | set(os_broken.index)
    all_os = sorted(list(all_os))
    
    # Align the data
    complete_counts = [os_complete.get(os, 0) for os in all_os]
    broken_counts = [os_broken.get(os, 0) for os in all_os]
    
    ax6 = axes[1, 2]
    x = np.arange(len(all_os))
    bars1 = ax6.bar(x - width/2, complete_counts, width, label='Complete', alpha=0.8)
    bars2 = ax6.bar(x + width/2, broken_counts, width, label='Broken', alpha=0.8)
    
    ax6.set_xlabel('Operating System')
    ax6.set_ylabel('Number of Participants')
    ax6.set_title('OS Distribution by Study Completion Status')
    ax6.set_xticks(x)
    ax6.set_xticklabels(all_os)
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('demographic_overview.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_completion_analysis(df, complete_df, broken_df):
    """Analyze study completion patterns and factors."""
    print("\nCreating completion analysis...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Study Completion Analysis', fontsize=16, fontweight='bold')
    
    # 1. Completion Rate by Demographics
    ax1 = axes[0, 0]
    
    # Calculate completion rates by age
    age_completion = df.groupby('age_group')['status'].apply(
        lambda x: (x == 'complete').sum() / len(x) * 100
    ).sort_index()
    
    bars = ax1.bar(age_completion.index, age_completion.values, alpha=0.8, color='steelblue')
    ax1.set_xlabel('Age Group')
    ax1.set_ylabel('Completion Rate (%)')
    ax1.set_title('Completion Rate by Age Group')
    ax1.set_ylim(0, 100)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom')
    
    # 2. Completion Rate by Education
    ax2 = axes[0, 1]
    
    edu_completion = df.groupby('education_level')['status'].apply(
        lambda x: (x == 'complete').sum() / len(x) * 100
    )
    
    bars = ax2.bar(edu_completion.index, edu_completion.values, alpha=0.8, color='darkgreen')
    ax2.set_xlabel('Education Level')
    ax2.set_ylabel('Completion Rate (%)')
    ax2.set_title('Completion Rate by Education Level')
    ax2.set_ylim(0, 100)
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # 3. Study Duration Analysis
    ax3 = axes[1, 0]
    
    # Filter out extreme outliers for better visualization
    duration_clean = complete_df[complete_df['study_duration_minutes'] < 200]['study_duration_minutes']
    
    ax3.hist(duration_clean, bins=30, alpha=0.7, color='purple', edgecolor='black')
    ax3.set_xlabel('Study Duration (minutes)')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Distribution of Study Duration (Complete Participants)')
    ax3.grid(True, alpha=0.3)
    
    # Add statistics
    mean_duration = duration_clean.mean()
    median_duration = duration_clean.median()
    ax3.axvline(mean_duration, color='red', linestyle='--', label=f'Mean: {mean_duration:.1f} min')
    ax3.axvline(median_duration, color='orange', linestyle='--', label=f'Median: {median_duration:.1f} min')
    ax3.legend()
    
    # 4. Screen Resolution Analysis
    ax4 = axes[1, 1]
    
    # Scatter plot of screen resolution
    complete_res = complete_df.dropna(subset=['screen_width', 'screen_height'])
    ax4.scatter(complete_res['screen_width'], complete_res['screen_height'], 
               alpha=0.6, s=50, color='teal')
    ax4.set_xlabel('Screen Width (pixels)')
    ax4.set_ylabel('Screen Height (pixels)')
    ax4.set_title('Screen Resolution Distribution (Complete Participants)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('completion_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_temporal_analysis(df):
    """Analyze temporal patterns in study participation."""
    print("\nCreating temporal analysis...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Temporal Analysis of Study Participation', fontsize=16, fontweight='bold')
    
    # 1. Daily participation over time
    ax1 = axes[0, 0]
    
    df['date'] = df['consent_timestamp'].dt.date
    daily_participation = df.groupby(['date', 'status']).size().unstack(fill_value=0)
    
    if 'complete' in daily_participation.columns and 'broken' in daily_participation.columns:
        daily_participation.plot(kind='bar', stacked=True, ax=ax1, alpha=0.8)
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Number of Participants')
        ax1.set_title('Daily Participation by Status')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(['Complete', 'Broken'])
        ax1.grid(True, alpha=0.3)
    
    # 2. Hourly participation pattern
    ax2 = axes[0, 1]
    
    df['hour'] = df['consent_timestamp'].dt.hour
    hourly_participation = df.groupby(['hour', 'status']).size().unstack(fill_value=0)
    
    if 'complete' in hourly_participation.columns and 'broken' in hourly_participation.columns:
        hourly_participation.plot(kind='line', ax=ax2, marker='o')
        ax2.set_xlabel('Hour of Day')
        ax2.set_ylabel('Number of Participants')
        ax2.set_title('Hourly Participation Pattern')
        ax2.set_xticks(range(0, 24, 2))
        ax2.legend(['Complete', 'Broken'])
        ax2.grid(True, alpha=0.3)
    
    # 3. Study duration vs completion time
    ax3 = axes[1, 0]
    
    complete_with_duration = df[(df['status'] == 'complete') & 
                               (df['study_duration_minutes'].notna()) & 
                               (df['study_duration_minutes'] < 200)]
    
    if not complete_with_duration.empty:
        ax3.scatter(complete_with_duration['consent_timestamp'], 
                   complete_with_duration['study_duration_minutes'], 
                   alpha=0.6, s=50, color='blue')
        ax3.set_xlabel('Consent Timestamp')
        ax3.set_ylabel('Study Duration (minutes)')
        ax3.set_title('Study Duration vs Start Time')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
    
    # 4. Completion rate by day of week
    ax4 = axes[1, 1]
    
    df['day_of_week'] = df['consent_timestamp'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    daily_completion = df.groupby('day_of_week')['status'].apply(
        lambda x: (x == 'complete').sum() / len(x) * 100
    ).reindex(day_order)
    
    bars = ax4.bar(daily_completion.index, daily_completion.values, alpha=0.8, color='coral')
    ax4.set_xlabel('Day of Week')
    ax4.set_ylabel('Completion Rate (%)')
    ax4.set_title('Completion Rate by Day of Week')
    ax4.set_ylim(0, 100)
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('temporal_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_technical_analysis(complete_df):
    """Analyze technical characteristics of participants."""
    print("\nCreating technical analysis...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Technical Characteristics Analysis', fontsize=16, fontweight='bold')
    
    # 1. Screen resolution distribution
    ax1 = axes[0, 0]
    
    # Create resolution categories
    complete_df['resolution_category'] = 'Other'
    complete_df.loc[(complete_df['screen_width'] == 1366) & (complete_df['screen_height'] == 768), 'resolution_category'] = '1366x768'
    complete_df.loc[(complete_df['screen_width'] == 1920) & (complete_df['screen_height'] == 1080), 'resolution_category'] = '1920x1080'
    complete_df.loc[(complete_df['screen_width'] == 1280) & (complete_df['screen_height'] == 800), 'resolution_category'] = '1280x800'
    complete_df.loc[(complete_df['screen_width'] == 1440) & (complete_df['screen_height'] == 900), 'resolution_category'] = '1440x900'
    complete_df.loc[(complete_df['screen_width'] == 1536) & (complete_df['screen_height'] == 864), 'resolution_category'] = '1536x864'
    
    resolution_counts = complete_df['resolution_category'].value_counts()
    
    wedges, texts, autotexts = ax1.pie(resolution_counts.values, labels=resolution_counts.index, 
                                      autopct='%1.1f%%', startangle=90)
    ax1.set_title('Screen Resolution Distribution')
    
    # 2. Browser version analysis
    ax2 = axes[0, 1]
    
    # Extract Chrome version
    chrome_users = complete_df[complete_df['browser'] == 'Chrome']
    chrome_users['chrome_version'] = chrome_users['user_agent'].str.extract(r'Chrome/(\d+)')
    chrome_version_counts = chrome_users['chrome_version'].value_counts().head(10)
    
    bars = ax2.bar(range(len(chrome_version_counts)), chrome_version_counts.values, alpha=0.8, color='green')
    ax2.set_xlabel('Chrome Version')
    ax2.set_ylabel('Number of Users')
    ax2.set_title('Chrome Version Distribution')
    ax2.set_xticks(range(len(chrome_version_counts)))
    ax2.set_xticklabels(chrome_version_counts.index, rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # 3. Screen area distribution
    ax3 = axes[1, 0]
    
    screen_area_clean = complete_df[complete_df['screen_area'] > 0]['screen_area']
    ax3.hist(screen_area_clean, bins=20, alpha=0.7, color='orange', edgecolor='black')
    ax3.set_xlabel('Screen Area (pixels²)')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Screen Area Distribution')
    ax3.grid(True, alpha=0.3)
    
    # 4. Touch capability analysis
    ax4 = axes[1, 1]
    
    touch_counts = complete_df['touch_capable'].value_counts()
    wedges, texts, autotexts = ax4.pie(touch_counts.values, labels=touch_counts.index, 
                                      autopct='%1.1f%%', startangle=90)
    ax4.set_title('Touch Capability Distribution')
    
    plt.tight_layout()
    plt.savefig('technical_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_statistical_summary(df, complete_df, broken_df):
    """Create comprehensive statistical summary tables."""
    print("\nCreating statistical summary...")
    
    # Summary statistics
    summary_stats = {
        'Total Participants': len(df),
        'Complete Participants': len(complete_df),
        'Broken/Incomplete Participants': len(broken_df),
        'Completion Rate (%)': round(len(complete_df)/len(df)*100, 2),
        'Average Study Duration (min)': round(complete_df['study_duration_minutes'].mean(), 2),
        'Median Study Duration (min)': round(complete_df['study_duration_minutes'].median(), 2),
        'Male Participants': len(df[df['gender'] == 'male']),
        'Female Participants': len(df[df['gender'] == 'female']),
        'Right-handed Participants': len(df[df['handedness'] == 'right']),
        'Left-handed Participants': len(df[df['handedness'] == 'left']),
        'Most Common Age Group': df['age_group'].mode().iloc[0] if not df['age_group'].mode().empty else 'N/A',
        'Most Common Education Level': df['education_level'].mode().iloc[0] if not df['education_level'].mode().empty else 'N/A',
        'Most Common Browser': df['browser'].mode().iloc[0] if not df['browser'].mode().empty else 'N/A',
        'Most Common OS': df['os'].mode().iloc[0] if not df['os'].mode().empty else 'N/A'
    }
    
    # Create summary table
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table data
    table_data = []
    for key, value in summary_stats.items():
        table_data.append([key, value])
    
    table = ax.table(cellText=table_data,
                    colLabels=['Metric', 'Value'],
                    cellLoc='left',
                    loc='center',
                    bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2)
    
    # Style the table
    for i in range(len(table_data) + 1):
        for j in range(2):
            cell = table[(i, j)]
            if i == 0:  # Header row
                cell.set_facecolor('#4CAF50')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
    
    ax.set_title('Study Demographics - Statistical Summary', fontsize=16, fontweight='bold', pad=20)
    plt.savefig('statistical_summary.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return summary_stats

def create_correlation_analysis(complete_df):
    """Create correlation analysis between different variables."""
    print("\nCreating correlation analysis...")
    
    # Select numeric columns for correlation
    numeric_cols = ['screen_width', 'screen_height', 'window_width', 'window_height', 
                   'screen_area', 'window_area', 'study_duration_minutes']
    
    # Create correlation matrix
    corr_matrix = complete_df[numeric_cols].corr()
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, 
                mask=mask,
                annot=True, 
                cmap='coolwarm', 
                center=0,
                square=True,
                fmt='.2f',
                cbar_kws={"shrink": .8})
    
    ax.set_title('Correlation Matrix of Technical Variables', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('correlation_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function to run the complete analysis."""
    print("="*60)
    print("Behavioral Biometrics Study")
    print("="*60)
    
    # File path
    file_path = '/Users/irentala/Documents/Harrisburgu/PHD_Courses/Main_Research/llm_scores_RK/2025-09-07_00-27-43_loris-mbp-cable-rcn-com/cleaned_data/desktop/metadata/metadata.csv'
    
    try:
        # Load and preprocess data
        df, complete_df, broken_df = load_and_preprocess_data(file_path)
        
        # Create visualizations
        create_demographic_overview(complete_df, broken_df)
        create_completion_analysis(df, complete_df, broken_df)
        create_temporal_analysis(df)
        create_technical_analysis(complete_df)
        create_correlation_analysis(complete_df)
        
        # Create statistical summary
        summary_stats = create_statistical_summary(df, complete_df, broken_df)
        
        # Print summary to console
        print("\n" + "="*60)
        print("STUDY SUMMARY STATISTICS")
        print("="*60)
        for key, value in summary_stats.items():
            print(f"{key}: {value}")
        
        print("\n" + "="*60)
        print("Analysis complete! All figures saved as PNG files.")
        print("="*60)
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
