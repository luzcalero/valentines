import json
import re
from datetime import datetime
import emoji
from collections import defaultdict, Counter

class MonthlyWhatsAppAnalyzer:
    def __init__(self, chat_file="_chat.txt"):
        self.chat_file = chat_file
        self.monthly_data = defaultdict(lambda: {
            'mora_mentions': 0,
            'besito_count': 0,
            'missing_expressions': 0,
            'emoji_usage': {
                'luz': Counter(),
                'andrea': Counter(),
                'total': Counter()
            },
            'people_mentions': defaultdict(int),
            'special_words': defaultdict(int)
        })
        
        # Define people to track
        self.people_patterns = {
            'clay': r'\bclay\b',  # Will be checked with date condition
            'pau': r'\b(?:pau\b|paula\b)',
            'sara': r'\bsara\b(?!h)',  # Excludes "sarah"
            'eden': r'\beden\b',
            'gabo': r'\bgabo\b(?:riel)?\b',
            'jaime': r'\bjaime\b',
            'isa': r'\b(?:isa\b|isabel\b)',
            'feli': r'\bfeli(?:pe)?\b',
            'nara': r'\bnara\b(?!n)',  # Excludes "naranja", "naranja", etc
            'marie': r'\bmarie\b',
            'pipia': r'\bpipia\b',
            'ana_valeria': r'\bana(?:\s+|-)?v(?:aleria)?\b|\bav\b',
            'stacy': r'\bstacy\b',
            'trinity': r'\btrinity\b',
            'marianna': r'\bmarianna?\b',
            'parents': r'\b(?:mami|papi|mama|papa)\b',
            'miranda': r'\bmiranda\b',
            'eloise': r'\beloise\b',
            'hayes': r'\bhayes\b',
            'emily': r'\bemily\b',
            'perry': r'\bperry\b',
            'leslie': r'\bleslie\b',
            'leila': r'\bleila\b',
            'alex': r'\balex(?:ander)?\b(?!a)',  # Excludes "alexa"
            'nina': r'\bnina\b',
            'mariela': r'\bmariela\b'
        }
        
        # Special words to track
        self.special_words = {
            'fronfis': r'\bfronfis\b',
            'proc': r'\bproc\b',
            'stroc': r'\bstroc\b',
            'guchta': r'\bguchta\b',
            'beba': r'\bbeba\b',
        }
        
    def process_message(self, date, sender, message):
        month_key = date.strftime('%Y-%m')
        message_lower = message.lower()
        sender_lower = sender.strip().lower()
        
        # Track Mora mentions
        if re.search(r'\bmora\b', message_lower):
            self.monthly_data[month_key]['mora_mentions'] += 1
        
        # Track "besito" mentions
        if re.search(r'\bbesito\b', message_lower):
            self.monthly_data[month_key]['besito_count'] += 1
            
        # Track missing expressions
        missing_patterns = [r'\bmiss you\b', r'\bmishu\b', r'\bte extraño\b', r'\bme haces falta\b']
        if any(re.search(pattern, message_lower) for pattern in missing_patterns):
            self.monthly_data[month_key]['missing_expressions'] += 1
            
        # Track emoji usage by sender
        emojis = [c for c in message if emoji.is_emoji(c)]
        if 'luz' in sender_lower:
            self.monthly_data[month_key]['emoji_usage']['luz'].update(emojis)
        elif 'andrea' in sender_lower:
            self.monthly_data[month_key]['emoji_usage']['andrea'].update(emojis)
        self.monthly_data[month_key]['emoji_usage']['total'].update(emojis)
        
        # Track people mentions
        for person, pattern in self.people_patterns.items():
            # Special handling for Clay (only count after 2024)
            if person == 'clay':
                if date.year >= 2024:
                    matches = len(re.findall(pattern, message_lower))
                    if matches > 0:
                        self.monthly_data[month_key]['people_mentions'][person] += matches
                continue
                
            matches = len(re.findall(pattern, message_lower))
            if matches > 0:
                self.monthly_data[month_key]['people_mentions'][person] += matches
                
        # Track special words
        for word, pattern in self.special_words.items():
            matches = len(re.findall(pattern, message_lower))
            if matches > 0:
                self.monthly_data[month_key]['special_words'][word] += matches

    def analyze_chat(self):
        date_pattern = r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\]\s*'
        message_pattern = date_pattern + r'([^:]+):\s*(.*?)(?=\[\d{1,2}/\d{1,2}/\d{2,4}|$)'
        
        with open(self.chat_file, 'r', encoding='utf-8') as file:
            content = file.read()
            
        for match in re.finditer(message_pattern, content, re.MULTILINE | re.DOTALL):
            date_str, sender, message = match.groups()
            try:
                date = datetime.strptime(date_str.strip(), '%m/%d/%y')
            except ValueError:
                try:
                    date = datetime.strptime(date_str.strip(), '%d/%m/%Y')
                except ValueError:
                    continue
                    
            self.process_message(date, sender.strip(), message.strip())
            
    def save_analysis(self, output_file='monthly_visualization_data.json'):
        output_data = {}
        for month, data in self.monthly_data.items():
            # Get top 3 emojis for each sender
            luz_emojis = dict(sorted(data['emoji_usage']['luz'].items(), 
                                   key=lambda x: x[1], 
                                   reverse=True)[:3])
            andrea_emojis = dict(sorted(data['emoji_usage']['andrea'].items(), 
                                      key=lambda x: x[1], 
                                      reverse=True)[:3])
            total_emojis = dict(sorted(data['emoji_usage']['total'].items(), 
                                     key=lambda x: x[1], 
                                     reverse=True)[:3])
            
            # Get top 5 people mentions sorted by frequency
            people_mentions = dict(sorted(data['people_mentions'].items(), 
                                        key=lambda x: x[1], 
                                        reverse=True)[:5])
            
            output_data[month] = {
                'mora_mentions': data['mora_mentions'],
                'besito_count': data['besito_count'],
                'missing_expressions': data['missing_expressions'],
                'top_emojis': {
                    'luz': luz_emojis,
                    'andrea': andrea_emojis,
                    'total': total_emojis
                },
                'people_mentions': people_mentions,
                'special_words': dict(data['special_words'])
            }
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

def main(input_file="_chat.txt", output_file="monthly_visualization_data.json", senders=None):
    analyzer = MonthlyWhatsAppAnalyzer(input_file)
    analyzer.analyze_chat()
    analyzer.save_analysis(output_file)

if __name__ == "__main__":
    main() 