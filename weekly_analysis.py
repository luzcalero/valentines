from daily_analysis import DailyWhatsAppAnalyzer
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
import json
import re

class WeeklyWhatsAppAnalyzer(DailyWhatsAppAnalyzer):
    def __init__(self, file_path, senders=None):
        super().__init__(file_path, senders)
    
    def get_week_key(self, date):
        # Get the Monday of the week for any given date
        monday = date - timedelta(days=date.weekday())
        return monday.isoformat()
    
    def analyze_weekly_patterns(self, df):
        # Normalize sender names in the dataframe
        df['sender'] = df['sender'].apply(self.normalize_sender_name)
        
        weekly_analysis = defaultdict(lambda: {
            sender: {
                'message_count': 0,
                'word_categories': defaultdict(int),
                'emoji_categories': defaultdict(int),
                'significant_words': defaultdict(int),
                'emojis': defaultdict(int),
                'emotion_intensity': defaultdict(int),
                'relationship_mentions': defaultdict(list),
                'sample_messages': [],
                'days_active': set()  # Track which days of the week had activity
            } for sender in self.senders
        })
        
        # Process each message
        for _, row in df.iterrows():
            date = row['timestamp'].date()
            week_key = self.get_week_key(date)
            sender = row['sender']
            
            if sender not in self.senders:
                continue
            
            # Add this day to the active days set
            weekly_analysis[week_key][sender]['days_active'].add(date.isoformat())
            
            # Increment message count
            weekly_analysis[week_key][sender]['message_count'] += 1
            
            if not row['is_media']:
                content = row['content'].lower()
                tokens = self.preprocess_text(content)
                
                # Analyze word categories
                for category, pattern in self.word_categories.items():
                    matches = len(list(re.finditer(pattern, content, re.IGNORECASE)))
                    if matches > 0:
                        weekly_analysis[week_key][sender]['word_categories'][category] += matches
                        
                        # Store context for relationship mentions
                        if category in ['mora'] + list(filter(lambda x: len(x) <= 5 or x in ['ana_valeria', 'parents'], self.word_categories.keys())):
                            weekly_analysis[week_key][sender]['relationship_mentions'][category].append(content)
                
                # Analyze emotion intensity
                for intensity_type, pattern in self.emotion_intensifiers.items():
                    matches = len(list(re.finditer(pattern, content, re.IGNORECASE)))
                    weekly_analysis[week_key][sender]['emotion_intensity'][intensity_type] += matches
                
                # Count significant words
                for word in tokens:
                    score = self.calculate_significance_score(word, 1, [content])
                    if score > 3:
                        weekly_analysis[week_key][sender]['significant_words'][word] += 1
                
                # Analyze emojis
                emojis = re.findall(r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF\u2700-\u27BF]', content)
                for emoji in emojis:
                    weekly_analysis[week_key][sender]['emojis'][emoji] += 1
                    for category, emoji_list in self.emoji_categories.items():
                        if emoji in emoji_list:
                            weekly_analysis[week_key][sender]['emoji_categories'][category] += 1
                
                # Store sample messages
                if len(weekly_analysis[week_key][sender]['sample_messages']) < 5:  # Store up to 5 messages per week
                    weekly_analysis[week_key][sender]['sample_messages'].append(content)
        
        return weekly_analysis
    
    def generate_visualization_data(self, df):
        weekly_patterns = self.analyze_weekly_patterns(df)
        
        visualization_data = {
            'timeline': [],
            'metadata': {
                'word_categories': list(self.word_categories.keys()),
                'emoji_categories': list(self.emoji_categories.keys()),
                'senders': self.senders,
                'relationship_categories': ['mora'] + list(filter(lambda x: len(x) <= 5, self.word_categories.keys()))
            }
        }
        
        # Sort weeks chronologically
        sorted_weeks = sorted(weekly_patterns.keys())
        
        for week in sorted_weeks:
            week_data = {
                'week_start': week,
                'senders': {}
            }
            
            # Check if any sender has messages this week
            has_messages = False
            for sender in self.senders:
                if weekly_patterns[week][sender]['message_count'] > 0:
                    has_messages = True
                    break
            
            if not has_messages:
                continue
            
            for sender in self.senders:
                sender_data = weekly_patterns[week][sender]
                week_data['senders'][sender] = {
                    'message_count': sender_data['message_count'],
                    'days_active': len(sender_data['days_active']),  # Number of active days
                    'word_categories': dict(sender_data['word_categories']),
                    'emoji_categories': dict(sender_data['emoji_categories']),
                    'emotion_intensity': dict(sender_data['emotion_intensity']),
                    'relationship_mentions': {
                        k: v[:3] for k, v in sender_data['relationship_mentions'].items()  # Keep only 3 sample contexts
                    },
                    'top_words': dict(sorted(
                        sender_data['significant_words'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:15]),  # Keep top 15 significant words for the week
                    'top_emojis': dict(sorted(
                        sender_data['emojis'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:7]),  # Keep top 7 emojis for the week
                    'sample_messages': sender_data['sample_messages']
                }
            
            visualization_data['timeline'].append(week_data)
        
        return visualization_data

def main(input_file, output_file, senders=None):
    print(f"Starting weekly analysis of {input_file}")
    
    # Initialize analyzer
    analyzer = WeeklyWhatsAppAnalyzer(input_file, senders)
    
    # Parse messages
    messages_df = analyzer.parse_messages()
    print(f"\nFound {len(messages_df)} messages")
    
    # Generate visualization data
    visualization_data = analyzer.generate_visualization_data(messages_df)
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(visualization_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nWeekly analysis saved to {output_file}") 