from initial_script import WhatsAppChatAnalyzer
import pandas as pd
from collections import defaultdict
import json
from datetime import datetime
import re

class DailyWhatsAppAnalyzer(WhatsAppChatAnalyzer):
    def __init__(self, file_path, senders=None):
        super().__init__(file_path)
        self.senders = senders or ['luz', 'andrea']  # Default senders
        
        # Name normalization mapping
        self.name_mapping = {
            'luz': 'luz',
            'andrea vega troncoso': 'andrea',
            'Andrea Vega Troncoso': 'andrea'
        }
        
        # Design system mappings - to be used by p5.js
        self.word_categories = {
            # Core relationship - Mora (our cat)
            'mora': r'mora+|michi|gatita|meow|purr|cat|gata',
            
            # Close friends and family
            'clay': r'clay',
            'pau': r'pau(?:la)?',
            'sara': r'sara',
            'eden': r'eden',
            'gabo': r'gabo',
            'jaime': r'jaime',
            'isa': r'\b(?:isa|isabel)\b',
            'feli': r'feli',
            'nara': r'nara',
            'marie': r'\bmarie\b',
            'pipia': r'pipia',
            'ana_valeria': r'ana\s*v(?:aleria)?',
            'stacy': r'stacy',
            'trinity': r'trinity',
            'marianna': r'marianna',
            'parents': r'mami|papi|mama|papa',
            'miranda': r'miranda',
            'eloise': r'eloise',
            'hayes': r'hayes',
            'emily': r'emily',
            'perry': r'perry',
            'leslie': r'leslie',
            'ana': r'\bana\b',
            'leila': r'leila',
            'alex': r'alex',
            'nina': r'nina',
            'mariela': r'\bmariela\b',  # Adding Mariela as a separate person
            
            # Love and affection expressions
            'love_expressions': r'te\s*amo|tqm|love\s*you|te\s*quiero|amor|bebe|bb|beibi|corazon|mi\s*vida',
            'terms_of_endearment': r'linda|hermosa|bonita|bella|linde|beba',
            'missing_each_other': r'miss\s*you|extrañ\w+|te\s*extraño|falta\w+|mishu',
            'cuddles': r'acoruque|arrunchis|ñoñ(?:o|ito)s?',
            'besito': r'besito',
            
            # Emotional states
            'happiness': r'feliz|happy|content|glad|yay|excited|emocionad',
            'sadness': r'sad|triste|crying|llor|miss',
            'worry': r'worried|preocupad|concern|cuidado',
            
            # Daily life and activities
            'home_life': r'casa|home|depa|apartment|room|cuarto',
            'food': r'comida|food|eat|comer|hungry|hambre',
            'sleep': r'dormir|sleep|tired|cansad|mimir',
            'work': r'work|trabajo|busy|ocupad',
            'bathroom': r'pupa|cagando|poop(?:ing)?|💩',
            
            # Special moments
            'celebration': r'birthday|cumpleaños|celebrate|celebr|party|fiesta',
            'plans': r'plan|weekend|meet|vernos|date',
            
            # Shared language
            'custom_expressions': r'fronfis|proc|stroc|guchta',
            'laughter': r'jaja+|haha+|lol|lmao|###LAUGH###',
        }
        
        # Emotion intensity markers
        self.emotion_intensifiers = {
            'high': r'super|muy|tan|más|mucho|really|so|such|totally',
            'repetition': r'(\w+[aeiou])\1+',  # Detects letter repetition like 'lindaaa'
        }
        
    def normalize_sender_name(self, sender):
        return self.name_mapping.get(sender, sender.lower())
    
    def analyze_daily_patterns(self, df):
        # Normalize sender names in the dataframe
        df['sender'] = df['sender'].apply(self.normalize_sender_name)
        
        daily_analysis = defaultdict(lambda: {
            sender: {
                'message_count': 0,
                'word_categories': defaultdict(int),
                'emoji_categories': defaultdict(int),
                'significant_words': defaultdict(int),
                'emojis': defaultdict(int),
                'emotion_intensity': defaultdict(int),
                'relationship_mentions': defaultdict(list),  # Track context of relationship mentions
                'sample_messages': []
            } for sender in self.senders
        })
        
        # Compile link pattern once for efficiency
        link_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        
        # Process each message
        for _, row in df.iterrows():
            date = row['timestamp'].date().isoformat()
            sender = row['sender']
            
            if sender not in self.senders:
                continue
                
            # Increment message count
            daily_analysis[date][sender]['message_count'] += 1
            
            if not row['is_media']:
                # Remove links before any analysis
                original_content = row['content']
                content_no_links = link_pattern.sub('', original_content)
                content = content_no_links.lower()  # Convert to lowercase for case-insensitive matching
                
                # Only process non-empty messages after link removal
                if content.strip():
                    tokens = self.preprocess_text(content)
                    
                    # Analyze word categories
                    for category, pattern in self.word_categories.items():
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        match_count = sum(1 for _ in matches)
                        if match_count > 0:
                            daily_analysis[date][sender]['word_categories'][category] += match_count
                            
                            # Store context for relationship mentions, but without links
                            if category in ['mora'] + list(filter(lambda x: len(x) <= 5 or x in ['ana_valeria', 'parents'], self.word_categories.keys())):
                                daily_analysis[date][sender]['relationship_mentions'][category].append(content_no_links)
                    
                    # Special handling for besito category when Andrea sends it to Luz
                    if sender == 'andrea' and re.search(r'besito', content, re.IGNORECASE):
                        daily_analysis[date][sender]['word_categories']['besito'] += 1
                    
                    # Analyze emotion intensity
                    for intensity_type, pattern in self.emotion_intensifiers.items():
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        daily_analysis[date][sender]['emotion_intensity'][intensity_type] += sum(1 for _ in matches)
                    
                    # Count significant words with improved scoring
                    # Skip words that look like parts of URLs
                    url_like = re.compile(r'^(?:https?|www|com|org|net|edu|gov|mil|biz|info|io|co|uk|us)$')
                    for word in tokens:
                        if not url_like.match(word):  # Skip URL-like words
                            base_score = self.calculate_significance_score(word, 1, [content])
                            
                            # Boost score based on context
                            if any(re.search(pattern, content, re.IGNORECASE) for pattern in self.word_categories['love_expressions'].split('|')):
                                base_score *= 1.5
                            if any(re.search(pattern, content, re.IGNORECASE) for pattern in self.word_categories['missing_each_other'].split('|')):
                                base_score *= 1.3
                            
                            if base_score > 3:  # Only track words above significance threshold
                                daily_analysis[date][sender]['significant_words'][word] += 1
                    
                    # Analyze emojis
                    emojis = re.findall(r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF\u2700-\u27BF]', content_no_links)
                    for emoji in emojis:
                        daily_analysis[date][sender]['emojis'][emoji] += 1
                        for category, emoji_list in self.emoji_categories.items():
                            if emoji in emoji_list:
                                daily_analysis[date][sender]['emoji_categories'][category] += 1
                    
                    # Store sample messages (up to 3 per day per sender), but without links
                    if len(daily_analysis[date][sender]['sample_messages']) < 3 and content_no_links.strip():
                        daily_analysis[date][sender]['sample_messages'].append(content_no_links)
        
        return daily_analysis
    
    def generate_visualization_data(self, df):
        daily_patterns = self.analyze_daily_patterns(df)
        
        # Convert to format suitable for p5.js visualization
        visualization_data = {
            'timeline': [],
            'metadata': {
                'word_categories': list(self.word_categories.keys()),
                'emoji_categories': list(self.emoji_categories.keys()),
                'senders': self.senders,
                'relationship_categories': ['mora'] + list(filter(lambda x: len(x) <= 5, self.word_categories.keys()))
            }
        }
        
        # Sort dates for chronological order
        sorted_dates = sorted(daily_patterns.keys())
        
        for date in sorted_dates:
            day_data = {
                'date': date,
                'senders': {}
            }
            
            # Check if any sender has messages on this day
            has_messages = False
            for sender in self.senders:
                if daily_patterns[date][sender]['message_count'] > 0:
                    has_messages = True
                    break
            
            if not has_messages:
                continue  # Skip days without messages
            
            for sender in self.senders:
                sender_data = daily_patterns[date][sender]
                day_data['senders'][sender] = {
                    'message_count': sender_data['message_count'],
                    'word_categories': dict(sender_data['word_categories']),
                    'emoji_categories': dict(sender_data['emoji_categories']),
                    'emotion_intensity': dict(sender_data['emotion_intensity']),
                    'relationship_mentions': {
                        k: v[:2] for k, v in sender_data['relationship_mentions'].items()  # Keep only 2 sample contexts
                    },
                    'top_words': dict(sorted(
                        sender_data['significant_words'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]),  # Keep top 10 significant words
                    'top_emojis': dict(sorted(
                        sender_data['emojis'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]),  # Keep top 5 emojis
                    'sample_messages': sender_data['sample_messages']
                }
            
            visualization_data['timeline'].append(day_data)
        
        return visualization_data

# Move main() outside the class
def main(input_file, output_file, senders=None):
    print(f"Starting analysis of {input_file}")
    
    # Initialize analyzer
    analyzer = DailyWhatsAppAnalyzer(input_file, senders)
    
    # Parse messages
    messages_df = analyzer.parse_messages()
    print(f"\nFound {len(messages_df)} messages")
    print(f"Date range: {messages_df['timestamp'].min()} to {messages_df['timestamp'].max()}")
    print(f"\nUnique senders: {messages_df['sender'].unique()}")
    
    # Generate visualization data
    print("\nGenerating visualization data...")
    viz_data = analyzer.generate_visualization_data(messages_df)
    
    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(viz_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nAnalysis complete. Results saved to {output_file}")
    print("\nSummary:")
    print(f"Total days analyzed: {len(viz_data['timeline'])}")
    
    # Print some sample data from the first day
    if viz_data['timeline']:
        first_day = viz_data['timeline'][0]
        print(f"\nSample data from {first_day['date']}:")
        for sender in viz_data['metadata']['senders']:
            if sender in first_day['senders']:
                sender_data = first_day['senders'][sender]
                print(f"\n{sender}:")
                print(f"Messages: {sender_data['message_count']}")
                print("Top categories:", dict(sorted(
                    sender_data['word_categories'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]))
    
    print("\nWord categories tracked:")
    for category in viz_data['metadata']['word_categories']:
        print(f"- {category}")
    print("\nEmoji categories tracked:")
    for category in viz_data['metadata']['emoji_categories']:
        print(f"- {category}")

if __name__ == "__main__":
    main('_chat.txt', 'daily_visualization_data.json', ['Luz', 'Andrea']) 