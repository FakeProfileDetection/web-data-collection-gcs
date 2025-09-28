#!/usr/bin/env python3
"""
This script generates visualizations specifically
on behavioral biometrics and keystroke dynamics.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set academic publication style
plt.style.use('default')
sns.set_style("whitegrid")

# Configure for academic publication
plt.rcParams.update({
    'figure.figsize': (10, 6),
    'font.size': 11,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'axes.grid': True,
    'grid.alpha': 0.3,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False
})

def load_data(file_path):
    """Load and preprocess the metadata."""
    df = pd.read_csv(file_path)
    
    # Convert timestamps
    df['submission_timestamp'] = pd.to_datetime(df['submission_timestamp'], errors='coerce')
    df['consent_timestamp'] = pd.to_datetime(df['consent_timestamp'], errors='coerce')
    
    # Calculate study duration
    df['study_duration_minutes'] = (df['submission_timestamp'] - df['consent_timestamp']).dt.total_seconds() / 60
    
    # Clean categorical variables
    df['age_group'] = df['age'].replace({
        '18_24': '18-24',
        '25_34': '25-34', 
        '35_44': '35-44',
        '45_54': '45-54',
        '55_64': '55-64'
    })
    
    df['education_level'] = df['education'].replace({
        'high_school': 'High School',
        'some_college': 'Some College',
        'bachelor': "Bachelor's",
        'masters': "Master's",
        'doctorate': 'Doctorate'
    })
    
    # Extract browser and OS info
    df['browser'] = df['user_agent'].str.extract(r'(Chrome|Firefox|Safari|Edge)')
    df['browser'] = df['browser'].fillna('Other')
    
    df['os'] = 'Windows'
    df.loc[df['user_agent'].str.contains('Macintosh', na=False), 'os'] = 'macOS'
    df.loc[df['user_agent'].str.contains('Linux', na=False), 'os'] = 'Linux'
    df.loc[df['user_agent'].str.contains('Android', na=False), 'os'] = 'Android'
    
    return df

def create_participant_flow_diagram(df):
    """Create a participant flow diagram for the methodology section."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    # Calculate flow numbers
    total_consented = len(df[df['consented'] == 'Yes'])
    total_complete = len(df[df['status'] == 'complete'])
    total_broken = len(df[df['status'] == 'broken'])
    
    # Create flow diagram
    y_positions = [0.8, 0.6, 0.4, 0.2]
    
    # Initial recruitment
    ax.text(0.1, y_positions[0], f'Initial Recruitment\n(n = {len(df)})', 
            ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
    
    # Consent
    ax.text(0.1, y_positions[1], f'Consented to Participate\n(n = {total_consented})', 
            ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
    
    # Complete
    ax.text(0.5, y_positions[2], f'Study Completed\n(n = {total_complete})\n({total_complete/len(df)*100:.1f}%)', 
            ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.7))
    
    # Broken/Incomplete
    ax.text(0.5, y_positions[3], f'Incomplete/Broken Data\n(n = {total_broken})\n({total_broken/len(df)*100:.1f}%)', 
            ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
    
    # Arrows
    ax.annotate('', xy=(0.1, y_positions[1]), xytext=(0.1, y_positions[0]),
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    ax.annotate('', xy=(0.5, y_positions[2]), xytext=(0.1, y_positions[1]),
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    ax.annotate('', xy=(0.5, y_positions[3]), xytext=(0.1, y_positions[1]),
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('Participant Flow Diagram', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('participant_flow_diagram.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_demographic_table(df):
    """Create a publication-quality demographic table."""
    # Filter complete participants with demographic data
    complete_demo = df[(df['status'] == 'complete') & 
                      (df['gender'].notna()) & 
                      (df['age'].notna()) & 
                      (df['education'].notna())]
    
    if len(complete_demo) == 0:
        print("No complete participants with demographic data found.")
        return
    
    # Create demographic summary
    demo_summary = {
        'Characteristic': ['Total Participants', 'Gender', '', '', 'Age Group', '', '', '', '', 
                          'Education Level', '', '', '', '', 'Handedness', '', ''],
        'Category': ['', 'Male', 'Female', 'Other', '18-24', '25-34', '35-44', '45-54', '55-64',
                    'High School', 'Some College', "Bachelor's", "Master's", 'Doctorate',
                    'Right', 'Left', 'Other'],
        'n (%)': ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
    }
    
    # Calculate counts and percentages
    total = len(complete_demo)
    demo_summary['n (%)'][0] = f"{total} (100.0)"
    
    # Gender
    gender_counts = complete_demo['gender'].value_counts()
    demo_summary['n (%)'][1] = f"{gender_counts.get('male', 0)} ({gender_counts.get('male', 0)/total*100:.1f})"
    demo_summary['n (%)'][2] = f"{gender_counts.get('female', 0)} ({gender_counts.get('female', 0)/total*100:.1f})"
    demo_summary['n (%)'][3] = f"{gender_counts.get('other', 0)} ({gender_counts.get('other', 0)/total*100:.1f})"
    
    # Age
    age_counts = complete_demo['age_group'].value_counts()
    for i, age in enumerate(['18-24', '25-34', '35-44', '45-54', '55-64']):
        count = age_counts.get(age, 0)
        demo_summary['n (%)'][5+i] = f"{count} ({count/total*100:.1f})"
    
    # Education
    edu_counts = complete_demo['education_level'].value_counts()
    for i, edu in enumerate(['High School', 'Some College', "Bachelor's", "Master's", 'Doctorate']):
        count = edu_counts.get(edu, 0)
        demo_summary['n (%)'][10+i] = f"{count} ({count/total*100:.1f})"
    
    # Handedness
    handed_counts = complete_demo['handedness'].value_counts()
    demo_summary['n (%)'][15] = f"{handed_counts.get('right', 0)} ({handed_counts.get('right', 0)/total*100:.1f})"
    demo_summary['n (%)'][16] = f"{handed_counts.get('left', 0)} ({handed_counts.get('left', 0)/total*100:.1f})"
    demo_summary['n (%)'][17] = f"{handed_counts.get('other', 0)} ({handed_counts.get('other', 0)/total*100:.1f})"
    
    # Create table
    fig, ax = plt.subplots(figsize=(8, 10))
    ax.axis('tight')
    ax.axis('off')
    
    table_data = list(zip(demo_summary['Characteristic'], demo_summary['Category'], demo_summary['n (%)']))
    
    table = ax.table(cellText=table_data,
                    colLabels=['Characteristic', 'Category', 'n (%)'],
                    cellLoc='left',
                    loc='center',
                    bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    
    # Style the table
    for i in range(len(table_data) + 1):
        for j in range(3):
            cell = table[(i, j)]
            if i == 0:  # Header row
                cell.set_facecolor('#4472C4')
                cell.set_text_props(weight='bold', color='white')
            elif demo_summary['Characteristic'][i-1] == '':  # Empty characteristic rows
                cell.set_facecolor('#f0f0f0')
            else:
                cell.set_facecolor('#ffffff')
    
    ax.set_title('Table 1: Demographic Characteristics of Study Participants', 
                fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('demographic_table.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_completion_rates_by_demographics(df):
    """Create completion rates by demographic characteristics."""
    # Filter participants with demographic data
    demo_data = df[(df['gender'].notna()) & (df['age'].notna()) & (df['education'].notna())]
    
    if len(demo_data) == 0:
        print("No participants with demographic data found.")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Gender completion rates
    gender_completion = demo_data.groupby('gender')['status'].apply(
        lambda x: (x == 'complete').sum() / len(x) * 100
    )
    
    bars1 = axes[0].bar(gender_completion.index, gender_completion.values, 
                       color=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.8)
    axes[0].set_title('Completion Rate by Gender')
    axes[0].set_ylabel('Completion Rate (%)')
    axes[0].set_ylim(0, 100)
    axes[0].grid(True, alpha=0.3)
    
    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
    
    # Age completion rates
    age_completion = demo_data.groupby('age_group')['status'].apply(
        lambda x: (x == 'complete').sum() / len(x) * 100
    ).sort_index()
    
    bars2 = axes[1].bar(age_completion.index, age_completion.values, 
                       color='#ff7f0e', alpha=0.8)
    axes[1].set_title('Completion Rate by Age Group')
    axes[1].set_ylabel('Completion Rate (%)')
    axes[1].set_ylim(0, 100)
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].grid(True, alpha=0.3)
    
    # Add value labels
    for bar in bars2:
        height = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
    
    # Education completion rates
    edu_completion = demo_data.groupby('education_level')['status'].apply(
        lambda x: (x == 'complete').sum() / len(x) * 100
    )
    
    bars3 = axes[2].bar(edu_completion.index, edu_completion.values, 
                       color='#2ca02c', alpha=0.8)
    axes[2].set_title('Completion Rate by Education Level')
    axes[2].set_ylabel('Completion Rate (%)')
    axes[2].set_ylim(0, 100)
    axes[2].tick_params(axis='x', rotation=45)
    axes[2].grid(True, alpha=0.3)
    
    # Add value labels
    for bar in bars3:
        height = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('completion_rates_demographics.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_technical_characteristics_summary(df):
    """Create technical characteristics summary for complete participants."""
    complete_df = df[df['status'] == 'complete']
    
    if len(complete_df) == 0:
        print("No complete participants found.")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Browser distribution
    browser_counts = complete_df['browser'].value_counts()
    axes[0, 0].pie(browser_counts.values, labels=browser_counts.index, autopct='%1.1f%%')
    axes[0, 0].set_title('Browser Distribution')
    
    # OS distribution
    os_counts = complete_df['os'].value_counts()
    axes[0, 1].pie(os_counts.values, labels=os_counts.index, autopct='%1.1f%%')
    axes[0, 1].set_title('Operating System Distribution')
    
    # Screen resolution (top 5)
    complete_df['resolution'] = complete_df['screen_width'].astype(str) + 'x' + complete_df['screen_height'].astype(str)
    resolution_counts = complete_df['resolution'].value_counts().head(5)
    
    bars = axes[1, 0].bar(range(len(resolution_counts)), resolution_counts.values, 
                         color='#1f77b4', alpha=0.8)
    axes[1, 0].set_title('Top 5 Screen Resolutions')
    axes[1, 0].set_ylabel('Number of Participants')
    axes[1, 0].set_xticks(range(len(resolution_counts)))
    axes[1, 0].set_xticklabels(resolution_counts.index, rotation=45)
    axes[1, 0].grid(True, alpha=0.3)
    
    # Study duration distribution
    duration_clean = complete_df[complete_df['study_duration_minutes'] < 10]['study_duration_minutes']
    axes[1, 1].hist(duration_clean, bins=20, color='#ff7f0e', alpha=0.8, edgecolor='black')
    axes[1, 1].set_title('Study Duration Distribution')
    axes[1, 1].set_xlabel('Duration (minutes)')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Add statistics
    mean_duration = duration_clean.mean()
    median_duration = duration_clean.median()
    axes[1, 1].axvline(mean_duration, color='red', linestyle='--', 
                      label=f'Mean: {mean_duration:.2f} min')
    axes[1, 1].axvline(median_duration, color='green', linestyle='--', 
                      label=f'Median: {median_duration:.2f} min')
    axes[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig('technical_characteristics.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_study_limitations_analysis(df):
    """Create analysis highlighting study limitations."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Completion rate over time
    df['date'] = df['consent_timestamp'].dt.date
    daily_completion = df.groupby('date')['status'].apply(
        lambda x: (x == 'complete').sum() / len(x) * 100
    )
    
    axes[0, 0].plot(daily_completion.index, daily_completion.values, 
                   marker='o', linewidth=2, markersize=6)
    axes[0, 0].set_title('Daily Completion Rate Over Time')
    axes[0, 0].set_ylabel('Completion Rate (%)')
    axes[0, 0].tick_params(axis='x', rotation=45)
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=27.2, color='red', linestyle='--', 
                      label=f'Overall Rate: 27.2%')
    axes[0, 0].legend()
    
    # Study duration vs completion
    complete_duration = df[df['status'] == 'complete']['study_duration_minutes']
    broken_duration = df[df['status'] == 'broken']['study_duration_minutes']
    
    axes[0, 1].hist([complete_duration[complete_duration < 5], 
                    broken_duration[broken_duration < 5]], 
                   bins=20, alpha=0.7, label=['Complete', 'Broken'],
                   color=['green', 'red'])
    axes[0, 1].set_title('Study Duration Distribution')
    axes[0, 1].set_xlabel('Duration (minutes)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Missing data analysis
    missing_data = {
        'Gender': df['gender'].isna().sum(),
        'Age': df['age'].isna().sum(),
        'Education': df['education'].isna().sum(),
        'Handedness': df['handedness'].isna().sum()
    }
    
    bars = axes[1, 0].bar(missing_data.keys(), missing_data.values(), 
                         color='orange', alpha=0.8)
    axes[1, 0].set_title('Missing Demographic Data')
    axes[1, 0].set_ylabel('Number of Missing Values')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{int(height)}', ha='center', va='bottom')
    
    # Data quality indicators
    quality_metrics = {
        'Complete Data': len(df[df['status'] == 'complete']),
        'Incomplete Data': len(df[df['status'] == 'broken']),
        'Valid Demographics': len(df[(df['gender'].notna()) & 
                                   (df['age'].notna()) & 
                                   (df['education'].notna())]),
        'Valid Duration': len(df[df['study_duration_minutes'].notna()])
    }
    
    bars = axes[1, 1].bar(quality_metrics.keys(), quality_metrics.values(), 
                         color='steelblue', alpha=0.8)
    axes[1, 1].set_title('Data Quality Metrics')
    axes[1, 1].set_ylabel('Number of Records')
    axes[1, 1].tick_params(axis='x', rotation=45)
    axes[1, 1].grid(True, alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('study_limitations_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function to generate Fake profile detection visualizations."""
    print("="*60)
    print("Behavioral Biometrics Study")
    print("="*60)
    
    # File path
    file_path = '/Users/irentala/Documents/Harrisburgu/PHD_Courses/Main_Research/llm_scores_RK/2025-09-07_00-27-43_loris-mbp-cable-rcn-com/cleaned_data/desktop/metadata/metadata.csv'
    
    try:
        # Load data
        df = load_data(file_path)
        
        print(f"Total participants: {len(df)}")
        print(f"Complete participants: {len(df[df['status'] == 'complete'])}")
        print(f"Completion rate: {len(df[df['status'] == 'complete'])/len(df)*100:.1f}%")
        
        # Generate visualizations
        create_participant_flow_diagram(df)
        create_demographic_table(df)
        create_completion_rates_by_demographics(df)
        create_technical_characteristics_summary(df)
        create_study_limitations_analysis(df)
        
        print("\n" + "="*60)
        print("Fake profile detection visualizations complete!")
        print("Generated files:")
        print("- participant_flow_diagram.png")
        print("- demographic_table.png")
        print("- completion_rates_demographics.png")
        print("- technical_characteristics.png")
        print("- study_limitations_analysis.png")
        print("="*60)
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
