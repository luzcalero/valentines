import re
import json
from datetime import datetime
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.collocations import BigramCollocationFinder
from collections import Counter, defaultdict

class WhatsAppChatAnalyzer:
    def __init__(self, file_path):
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('punkt_tab')
        
        # Initialize lemmatizer
        self.lemmatizer = WordNetLemmatizer()
        
        # Initialize Spanish and English stopwords
        self.stop_words = set(stopwords.words('spanish') + stopwords.words('english'))
        
        # Custom words to ignore
        self.ignore_words = {'image', 'video', 'omitted', 'audio', 'document'}
        
        # Emoji categories
        self.emoji_categories = {
            'love': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💗', '💓', '💕', '💖', '💝', '💘', '💞', '💟'],
            'affection': ['😘', '🥰', '😍', '☺️', '😊', '🤗', '💑', '💏'],
            'happiness': ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '🙂'],
            'sadness': ['😢', '😭', '😥', '😔', '😞', '😟', '😩', '😫'],
            'tenderness': ['🥺'],
            'anger': ['😠', '😡', '🤬', '😤', '😾'],
            'surprise': ['😮', '😯', '😲', '😱', '🤯'],
            'nature': ['🌺', '🌸', '🌼', '🌻', '🌹', '🌷', '🌿', '☘️', '🍀'],
            'celebration': ['🎉', '🎊', '🎈', '✨', '💫', '⭐️', '🌟'],
            'other': []  # For uncategorized emojis
        }
        
        # Add emotional and significant word patterns
        self.significant_patterns = {
            'terms_of_endearment': r'(?i)(bebe|bb|amor|linda|hermosa|bonita|beibi|corazon|mi vida|cielo|princesa)',
            'custom_expressions': r'(?i)(fronfis|proc)',  # Add your custom words here
            'diminutives': r'(?i)\w+[it]a\b|\w+[it]o\b|\w+[it]e\b',  # Words ending in ita/ito/ite
            'intensifiers': r'(?i)(super|muy|tan|más|mucho)',
            'emotional_markers': r'(?i)(te amo|te quiero|extraño|miss you|tqm|love|❤️|😘|🥰|💕|💗|💖)',
            'significant_people': r'(?i)(gabo|clay|pau(?:la)?|sara|eden|pipia|nara|marie|feli|isa|jaime|camila|mora)'
        }   
        
        # Weight factors for scoring significance
        self.significance_weights = {
            'terms_of_endearment': 5,
            'custom_expressions': 4,
            'diminutives': 3,
            'intensifiers': 2,
            'emotional_markers': 5,
            'frequency': 1,
            'significant_people': 10
        }
        
        # Read and parse the chat file
        with open(file_path, 'r', encoding='utf-8') as file:
            self.raw_text = file.read()

    def parse_messages(self):
        # Regular expression for WhatsApp message format
        pattern = r'\[(\d{1,2}/\d{1,2}/\d{2},\s\d{1,2}:\d{2}:\d{2}\s[AP]M)\]\s(.*?):\s(.*?)(?=\n\[\d{1,2}/\d{1,2}/\d{2}|\Z)'
        
        messages = []
        for match in re.finditer(pattern, self.raw_text, re.DOTALL):
            timestamp_str, sender, content = match.groups()
            
            # Parse timestamp
            timestamp = datetime.strptime(timestamp_str, '%m/%d/%y, %I:%M:%S %p')
            
            # Skip system messages
            if 'Messages and calls are end-to-end encrypted' in content:
                continue
                
            messages.append({
                'timestamp': timestamp,
                'sender': sender.strip(),
                'content': content.strip(),
                'is_media': any(word in content.lower() for word in self.ignore_words)
            })
        
        return pd.DataFrame(messages)

    def preprocess_text(self, text):
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Consolidate common expressions before tokenization
        text = re.sub(r'(?i)(?:ha|ja|he|je){2,}|(?:ha|ja|he|je)(?:ha|ja|he|je)+|lol|lmao', '###LAUGH###', text)  # Modified laughter pattern
        text = re.sub(r'(?i)aw+', 'AW', text)  # Consolidate awwww variations
        text = re.sub(r'(?i)si+', 'SI', text)  # Consolidate siii variations
        text = re.sub(r'(?i)hola+', 'HOLA', text)  # Consolidate holaaa variations
        text = re.sub(r'(?i)\bq\b', 'que', text)  # Replace q with que
        text = re.sub(r'(?i)\bu\b', 'you', text)  # Replace u with you
        text = re.sub(r'(?i)\bbb\b', 'bebe', text)  # Replace bb with bebe
        text = re.sub(r'(?i)lind[ae]+', 'LINDA', text)  # Consolidate linda variations
        text = re.sub(r'(?i)li+nd[ae]', 'LINDE', text)  # Consolidate linde variations
        
        # Tokenize
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords, ignored words, and lemmatize
        processed_tokens = [
            self.lemmatizer.lemmatize(token.replace('###laugh###', 'LAUGH'))
            for token in tokens
            if token.isalnum() and 
            token not in self.stop_words and 
            token not in self.ignore_words
        ]
        
        return processed_tokens

    def calculate_significance_score(self, word, frequency, content_samples):
        score = frequency * self.significance_weights['frequency']
        
        # Check if word matches any significant patterns
        for pattern_type, pattern in self.significant_patterns.items():
            if re.search(pattern, word):
                score += self.significance_weights[pattern_type] * frequency
        
        # Bonus points for words that appear in emotional contexts
        for sample in content_samples[:10]:  # Check up to 10 sample contexts
            for pattern_type, pattern in self.significant_patterns.items():
                if re.search(pattern, sample):
                    score += self.significance_weights[pattern_type]
        
        return score

    def analyze_text(self, df):
        word_timeline = defaultdict(list)
        word_frequencies = Counter()
        content_samples = defaultdict(list)
        
        # Process each message
        for _, row in df.iterrows():
            if not row['is_media']:
                tokens = self.preprocess_text(row['content'])
                
                # Update word frequencies, timeline, and content samples
                for token in tokens:
                    word_frequencies[token] += 1
                    word_timeline[token].append(row['timestamp'])
                    if len(content_samples[token]) < 10:  # Keep up to 10 sample contexts
                        content_samples[token].append(row['content'])

        # Calculate significance scores and create analysis results
        analysis_results = {}
        
        for word, freq in word_frequencies.items():
            timestamps = word_timeline[word]
            if timestamps:
                significance_score = self.calculate_significance_score(
                    word, freq, content_samples[word]
                )
                analysis_results[word] = {
                    "frequency": freq,
                    "significance_score": significance_score,
                    "first_appearance": min(timestamps).isoformat(),
                    "peak_usage": max(timestamps).isoformat(),
                    "sample_contexts": content_samples[word][:3]  # Include up to 3 sample contexts
                }

        return analysis_results

    def analyze_temporal_patterns(self, df):
        # Group messages by hour and day
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day_name()
        
        temporal_patterns = {
            'hourly_activity': df['hour'].value_counts().to_dict(),
            'daily_activity': df['day'].value_counts().to_dict(),
            'message_density': {
                str(date): count
                for date, count in df.groupby(df['timestamp'].dt.date).size().items()
            }
        }
        
        return temporal_patterns

    def analyze_emojis(self, df):
        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF\u2700-\u27BF]')
        emoji_stats = {
            'total_count': 0,
            'by_category': defaultdict(int),
            'individual_counts': defaultdict(int),
            'most_used_combinations': defaultdict(int),
            'timeline': defaultdict(list)
        }
        
        for _, row in df.iterrows():
            if not row['is_media']:
                # Find all emojis in the message
                emojis = emoji_pattern.findall(row['content'])
                if emojis:
                    # Update total count
                    emoji_stats['total_count'] += len(emojis)
                    
                    # Count individual emojis
                    for emoji in emojis:
                        emoji_stats['individual_counts'][emoji] += 1
                        emoji_stats['timeline'][emoji].append(row['timestamp'].isoformat())
                        
                        # Categorize emoji
                        categorized = False
                        for category, emoji_list in self.emoji_categories.items():
                            if emoji in emoji_list:
                                emoji_stats['by_category'][category] += 1
                                categorized = True
                                break
                        if not categorized:
                            emoji_stats['by_category']['other'] += 1
                    
                    # Count emoji combinations (if multiple emojis in message)
                    if len(emojis) > 1:
                        combo = ''.join(emojis)
                        emoji_stats['most_used_combinations'][combo] += 1
        
        # Convert defaultdict to regular dict for JSON serialization
        emoji_stats['by_category'] = dict(emoji_stats['by_category'])
        emoji_stats['individual_counts'] = dict(emoji_stats['individual_counts'])
        emoji_stats['most_used_combinations'] = dict(
            sorted(emoji_stats['most_used_combinations'].items(), 
                  key=lambda x: x[1], 
                  reverse=True)[:10]  # Keep only top 10 combinations
        )
        emoji_stats['timeline'] = dict(emoji_stats['timeline'])
        
        return emoji_stats

def main(input_file, output_file):
    # Initialize analyzer
    analyzer = WhatsAppChatAnalyzer(input_file)
    
    # Parse and analyze messages
    messages_df = analyzer.parse_messages()
    word_analysis = analyzer.analyze_text(messages_df)
    temporal_patterns = analyzer.analyze_temporal_patterns(messages_df)
    emoji_analysis = analyzer.analyze_emojis(messages_df)
    
    # Convert word analysis to DataFrame
    word_analysis_df = pd.DataFrame.from_dict(word_analysis, orient='index')
    
    # Sort by significance score and get top 100 words
    top_100_words = word_analysis_df.sort_values('significance_score', ascending=False).head(100)
    
    # Print significant word analysis
    print("Top 100 Most Significant Words:")
    print("-" * 80)
    print(f"{'Word':<20} {'Significance':<12} {'Frequency':<10} {'Sample Context':<30}")
    print("-" * 80)
    
    for word, row in top_100_words.iterrows():
        sample_context = row['sample_contexts'][0][:30] + '...' if row['sample_contexts'] else ''
        print(f"{word:<20} {row['significance_score']:<12.2f} {row['frequency']:<10} {sample_context}")
    
    # Print emoji analysis summary
    print("\nEmoji Analysis Summary:")
    print("-" * 80)
    print(f"Total Emojis Used: {emoji_analysis['total_count']}")
    
    print("\nMost Used Emojis:")
    print("-" * 80)
    sorted_emojis = sorted(emoji_analysis['individual_counts'].items(), key=lambda x: x[1], reverse=True)
    for emoji, count in sorted_emojis[:15]:  # Show top 15 emojis
        print(f"{emoji}: {count} times")
    
    print("\nEmojis by Category:")
    print("-" * 80)
    for category, count in emoji_analysis['by_category'].items():
        print(f"{category.capitalize()}: {count}")
    
    print("\nTop Emoji Combinations:")
    print("-" * 80)
    for combo, count in list(emoji_analysis['most_used_combinations'].items())[:5]:  # Show top 5 combinations
        print(f"{combo}: {count} times")
    
    # Save full results
    analysis_results = {
        'word_analysis': word_analysis,
        'temporal_patterns': temporal_patterns,
        'emoji_analysis': emoji_analysis
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main('_chat.txt', 'chat_analysis.json')