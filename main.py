import argparse
from initial_script import WhatsAppChatAnalyzer
from daily_analysis import main as analyze_chat_daily
from weekly_analysis import main as analyze_chat_weekly
from monthly_analysis import main as analyze_chat_monthly

def main():
    parser = argparse.ArgumentParser(description='WhatsApp Chat Analysis Tools')
    parser.add_argument('--input', '-i', default='_chat.txt',
                       help='Path to the WhatsApp chat export file (default: _chat.txt)')
    parser.add_argument('--output', '-o', default='daily_visualization_data.json',
                       help='Output file path (default: daily_visualization_data.json)')
    parser.add_argument('--type', '-t', choices=['basic', 'daily', 'weekly', 'monthly'], default='daily',
                       help='Type of analysis to perform (default: daily)')
    parser.add_argument('--senders', '-s', nargs='+',
                       help='Sender names for analysis (default: ["Luz", "Andrea"])')
    
    args = parser.parse_args()
    
    if args.type == 'basic':
        # Run basic analysis
        WhatsAppChatAnalyzer.main(args.input, args.output)
    elif args.type == 'weekly':
        # Run weekly analysis
        analyze_chat_weekly(args.input, args.output, args.senders)
    elif args.type == 'monthly':
        # Run monthly analysis
        analyze_chat_monthly(args.input, args.output, args.senders)
    else:
        # Run daily analysis
        analyze_chat_daily(args.input, args.output, args.senders)

if __name__ == '__main__':
    main() 