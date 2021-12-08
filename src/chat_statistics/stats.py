import json
import re
from pathlib import Path
from typing import Union

import arabic_reshaper
import demoji
from bidi.algorithm import get_display
from hazm import Normalizer, word_tokenize
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
            stop_words = list(map(str.strip, stop_words))
            self.stop_words = list(map(self.normalizer.normalize, stop_words))

    def generate_word_cloud(
        self,
        ouput_dir: Union[str, Path],
        width: int = 800,
        height: int = 600,
        max_font_size = 250,
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
            width=1200, height=1200,
            font_path=str(DATA_DIR / "./BHoma.ttf"),
            background_color='white',
            max_font_size=250
            ).generate(text_content)

        logger.info(f"Saving word cload to {Path(ouput_dir) / 'wordcload.png'}")
        wordcloud.to_file(str(Path(ouput_dir) / 'wordcloud.png'))

if __name__ == "__main__":
    chat_stats = ChatStatistics(chat_json=DATA_DIR / 'online.json')
    chat_stats.generate_word_cloud(ouput_dir=DATA_DIR)


print("Done!")
