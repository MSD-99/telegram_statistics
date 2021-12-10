import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Union

import arabic_reshaper
import demoji
from bidi.algorithm import get_display
from hazm import Normalizer, sent_tokenize, word_tokenize
from loguru import logger
from src.data import DATA_DIR
from wordcloud import WordCloud


#
class ChatStatistics:
    """
        Generates chat statistics from a telegram chat json file
    """
    def __init__(self, chat_json: Union[str, Path] ):
        """
        :param chat_json: path to telegram export json file
        """
        #load chat data
        logger.info(f"Loading chat data from {chat_json}")
        with open(Path(chat_json)) as f:
            self.chat_data = json.load(f)


        self.normalizer = Normalizer()
        
        #load stopwords
        logger.info(f"Loading stopwords from {DATA_DIR / 'stop_words.txt'}")
        with open (DATA_DIR / 'stop_words.txt') as stop:
            stop_words = stop.readlines()
            stop_words = map(str.strip, stop_words)
            self.stop_words = set(map(self.normalizer.normalize, stop_words))

    @staticmethod
    def rebuild_msg(sub_messages):
        """
        
        """
        msg_text = ''
        for sub_msg in sub_messages:
            if isinstance(sub_msg,str):
                msg_text += sub_msg
            elif 'text' in sub_msg:
                msg_text +=sub_msg['text']
    
        return msg_text

    def msg_has_question(self, msg):
        """Checks if a message has a question

        :parm msg: message ti check
        """

        if not isinstance(msg['text'], str):
            msg['text'] = self.rebuild_msg(msg['text'])
            
        sentences =sent_tokenize(msg['text'])
        for sent in sentences:
            if ('؟' not in sent) and ('?' not in sent):
                continue
                
            return True

    def get_top_users(self, top_n: int = 10) -> dict:
        """Get top n users from the chat

        :param top_n: number of users to get, default to 10
        :return: dict of top users
        """
        logger.info("Getting top users...")
        # check messages for questions
        is_question = defaultdict(bool)
        for msg in self.chat_data['messages']:
            if not isinstance(msg['text'], str):
                msg['text'] = self.rebuild_msg(msg['text'])
                
            sentences =sent_tokenize(msg['text'])
            for sent in sentences:
                if ('؟' not in sent) and ('?' not in sent):
                    continue
                    
                is_question[msg['id']] = True
                break
        # get top users based on replying to questions from others
        users = []
        for msg in self.chat_data['messages']:
            if not msg.get('reply_to_message_id'):
                continue
            
            if is_question[msg['reply_to_message_id']] is False:
                continue 
                
            users.append(msg['from'])

        return dict(Counter(users).most_common(top_n))



    def generate_word_cloud(
        self,
        ouput_dir: Union[str, Path],
        width: int = 1200,height: int = 800,
        max_font_size: int = 250,
        background_color: str = 'white',
        ):
        """Generates a word cloud from the chat data

        :parm output_dir: path to output diractory for word cloud image
        """
        logger.info("Loading text content ...")
        text_content = ''
        for msg in self.chat_data['messages']:
            if type(msg['text']) is str:
                tokens = word_tokenize(msg['text'])
                tokens = list(filter(lambda item: item not in self.stop_words, tokens))
                text_content +=f" {' '.join(tokens)}"


        # reomove emojies from text_content
        def deEmojify(text):
            regrex_pattern = re.compile(pattern = "["
                "\u2069"
                "\u2066"
                        "]+", flags = re.UNICODE)
            return demoji.replace(regrex_pattern.sub(r' ',text), " ")

        # normalize, reshape for final word cloud
        text_content = self.normalizer.normalize(text_content)
        for _ in range(2):
            text_content = arabic_reshaper.reshape(text_content)
            text_content = get_display(deEmojify(text_content))
        


        # Generate word cloud
        logger.info("Generating word cload")
        wordcloud = WordCloud(
            width=width, height=height,
            font_path=str(DATA_DIR / "./BHoma.ttf"),
            background_color=background_color,
            max_font_size=max_font_size,
            ).generate(text_content)

        logger.info(f"Saving word cload to {Path(ouput_dir) / 'wordcload.png'}")
        wordcloud.to_file(str(Path(ouput_dir) / 'wordcloud.png'))

if __name__ == "__main__":
    chat_stats = ChatStatistics(chat_json=DATA_DIR / 'online.json')
    chat_stats.generate_word_cloud(ouput_dir=DATA_DIR)
    top_users = chat_stats.get_top_users(top_n=10)
    print(top_users)

    print("Done!")
